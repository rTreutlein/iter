# Iter

Run from the repository directory with Python 3.

## Use a Claude subscription

With Claude Code installed, sign in once with your subscription account and start Iter:

```bash
claude auth login
ITER_BACKEND=claude python3 iter.py
```

If already signed in, skip the login command. Set `CLAUDE_MODEL` to select a model or leave it unset for the CLI default. Each step, including autonomous work, sends Iter’s assembled conversation, memory, and tool definitions to Claude Code. Iter runs the selected tools locally. Press Ctrl+C to stop. [Claude Code authentication](https://code.claude.com/docs/en/authentication)

## Use a Codex subscription

Install the Codex CLI, then run the following from the repository directory:

```bash
codex login
ITER_BACKEND=codex python3 iter.py
```

Choose **Sign in with ChatGPT** using an account with Codex access. If you already signed in, skip the login step. Check the current login with `codex login status`.

Each Iter step sends its assembled conversation, memory, and tool definitions to Codex and uses your plan allowance, including during autonomous work. Iter executes the returned tool calls locally. The CLI selects its default model unless you set `CODEX_MODEL`. Press Ctrl+C to stop.

See the [official OpenAI documentation for Codex authentication](https://developers.openai.com/codex/auth).
