"""Select Iter tool calls through a signed-in Claude Code CLI."""

import json
import os
import subprocess
import tempfile
import uuid


def _run(args, timeout, prompt=None):
    env = os.environ.copy()
    for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"):
        env.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="iter-claude-") as directory:
        result = subprocess.run(
            ["claude", "--safe-mode", "--setting-sources", "", *args],
            input=prompt, capture_output=True, encoding="utf-8",
            cwd=directory, env=env, timeout=timeout,
        )
    try:
        reply = json.loads(result.stdout)
    except ValueError:
        raise RuntimeError(result.stderr.strip()[-500:] or "Claude returned invalid JSON") from None
    if result.returncode or reply.get("is_error"):
        raise RuntimeError(reply.get("result") or result.stderr.strip()[-500:] or "Claude request failed")
    return reply


def check_login():
    try:
        status = _run(["auth", "status"], 15)
    except FileNotFoundError:
        raise SystemExit("Install Claude Code and run claude auth login.") from None
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        raise SystemExit(f"Check Claude Code with claude auth login. {error}") from None
    if not status.get("loggedIn") or status.get("authMethod") not in ("claude.ai", "oauth_token"):
        raise SystemExit("Run claude auth login with your Claude subscription account.")


def next_message(messages, tools, model, timeout):
    if not tools:
        raise ValueError("Claude needs at least one available Iter tool")
    variants = []
    for tool in tools:
        function = tool["function"]
        variants.append({
            "type": "object",
            "properties": {
                "name": {"type": "string", "enum": [function["name"]]},
                "arguments": function["parameters"],
            },
            "required": ["name", "arguments"],
            "additionalProperties": False,
        })
    schema = {
        "type": "object",
        "properties": {"calls": {"type": "array", "items": {"anyOf": variants}}},
        "required": ["calls"],
        "additionalProperties": False,
    }
    args = [
        "--print", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
        "--output-format", "json", "--json-schema", json.dumps(schema),
        "--system-prompt", "Select one or more next tool calls for Iter using the supplied "
        "conversation and tool definitions. Iter executes the calls.",
    ]
    if model:
        args.extend(["--model", model])
    reply = _run(args, timeout, json.dumps({"messages": messages, "tools": tools}, ensure_ascii=False))
    output = reply.get("structured_output") or {}
    if not output.get("calls"):
        raise RuntimeError("Claude returned no structured Iter tool calls")
    return {
        "role": "assistant",
        "tool_calls": [
            {"id": "call_" + uuid.uuid4().hex, "type": "function",
             "function": {"name": call["name"], "arguments": json.dumps(call["arguments"], ensure_ascii=False)}}
            for call in output["calls"]
        ],
    }
