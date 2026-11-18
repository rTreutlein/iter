"""Use the signed-in Codex CLI for one Iter decision at a time."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid


def next_message(messages, tools, model, timeout):
    names = [tool["function"]["name"] for tool in tools]
    if not names:
        raise ValueError("Codex needs at least one available Iter tool")
    schema = {
        "type": "object",
        "properties": {
            "calls": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "enum": names},
                        "arguments": {"type": "string"},
                    },
                    "required": ["name", "arguments"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["calls"],
        "additionalProperties": False,
    }
    prompt = (
        "Choose the next tool call(s) for Iter using the supplied conversation and tool "
        "definitions. Return at least one call. Encode each arguments object as a JSON "
        "string. Iter will execute the calls. Use only the supplied context and tools.\n"
        + json.dumps({"messages": messages, "tools": tools}, ensure_ascii=False)
    )
    with tempfile.TemporaryDirectory(prefix="iter-codex-") as directory:
        schema_path = Path(directory, "schema.json")
        output_path = Path(directory, "reply.json")
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        command = [
            "codex", "exec", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
            "--sandbox", "read-only", "-c", 'forced_login_method="chatgpt"',
            "-c", 'model_provider="openai"', "--output-schema", str(schema_path),
            "--output-last-message", str(output_path),
        ]
        if model:
            command.extend(["--model", model])
        env = os.environ.copy()
        for key in ("CODEX_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL"):
            env.pop(key, None)
        result = subprocess.run(command + ["-"], input=prompt, encoding="utf-8",
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                cwd=directory, env=env, timeout=timeout)
        if result.returncode:
            errors = [line for line in result.stderr.splitlines() if "error" in line.lower()]
            detail = errors[-1][:400] if errors else f"exit code {result.returncode}"
            raise RuntimeError(f"Codex exec failed ({detail})")
        calls = json.loads(output_path.read_text(encoding="utf-8"))["calls"]
    return {
        "role": "assistant",
        "tool_calls": [
            {"type": "function", "id": "call_" + uuid.uuid4().hex, "function": call}
            for call in calls
        ],
    }
