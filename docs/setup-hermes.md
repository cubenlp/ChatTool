# chattool setup hermes

`chattool setup hermes` installs Hermes Agent, optionally prepares Hermes WebUI, and writes Hermes configuration from ChatTool typed env profiles.

## What It Installs

Default targets:

- Agent checkout: `./hermes` when run from a project containing that directory, otherwise `~/.hermes/hermes-agent`.
- WebUI checkout: `./hermes-webui` when run from a project containing that directory, otherwise `~/.hermes/hermes-webui`.
- Runtime: `venv` inside the Hermes Agent checkout.
- CLI link: `~/.local/bin/hermes` -> `<agent-dir>/venv/bin/hermes`.
- State and credentials: `~/.hermes/`.

Default Hermes extras are intentionally lightweight:

```text
messaging,cli,pty,cron,feishu,web,acp,mcp
```

This avoids the heavier official `.[all]` path, which includes optional RL, voice, browser, and other dependencies that are not required for a basic Agent + WebUI + Feishu setup.

## Configuration Sources

OpenAI-compatible model settings are resolved from:

1. Explicit CLI flags: `--api-key`, `--base-url`, `--model`.
2. `-e/--env`: OpenAI `.env` path or saved OpenAI profile name.
3. Current shell environment.
4. Active ChatTool OpenAI typed env.
5. Defaults: `https://api.openai.com/v1`, `gpt-5.4-mini`.

Feishu settings are resolved from:

1. `--feishu-env`: Feishu `.env` path or saved Feishu profile name.
2. Current shell environment.
3. Active ChatTool Feishu typed env.

The command writes:

- `~/.hermes/.env` for credentials and provider env vars.
- `~/.hermes/config.yaml` for model, provider, and terminal defaults.
- `<webui-dir>/.env` for WebUI discovery and local binding.

Secrets are written locally and should not be committed.

## Usage

Preview actions without writing files:

```bash
chattool setup hermes --dry-run -I
```

Install in the current research project and reuse active ChatTool env profiles:

```bash
chattool setup hermes --agent-dir ./hermes --webui-dir ./hermes-webui
```

Use named profiles:

```bash
chattool setup hermes -e apple --feishu-env rexwzh
```

Install and start WebUI:

```bash
chattool setup hermes --agent-dir ./hermes --webui-dir ./hermes-webui --start-webui
```

Only install dependencies and CLI link, without writing model or Feishu config:

```bash
chattool setup hermes --install-only
```

## WebUI Binding Model

A single Hermes WebUI server process binds to one Hermes Agent runtime via:

- `HERMES_WEBUI_AGENT_DIR`
- `HERMES_WEBUI_PYTHON`
- `HERMES_HOME`
- `HERMES_CONFIG_PATH`

That WebUI can still contain multiple sessions, workspaces, and profiles. To run multiple isolated Hermes backends, start multiple WebUI processes on different ports with different `HERMES_HOME` / `HERMES_WEBUI_AGENT_DIR` values.

## Verification

After setup:

```bash
hermes version
hermes status
hermes doctor
hermes -z 'Reply with exactly: HERMES_OK' --ignore-rules
curl --noproxy '*' http://127.0.0.1:8787/health
```

If a local proxy is configured, use `--noproxy '*'` or set `NO_PROXY=127.0.0.1,localhost` for local WebUI health checks.
