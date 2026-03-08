from pathlib import Path
import click
from chattool.utils.tui import is_interactive_available, ask_select, ask_path, BACK_VALUE

TEMPLATES = {}
ENV_DEFAULTS = {}

TEMPLATES["chromium"] = """services:
  chromium:
    image: ${IMAGE}
    container_name: ${CONTAINER_NAME}
    restart: ${RESTART_POLICY}
    ports:
      - "${BIND_IP}:${PORT}:3000"
    environment:
      TOKEN: ${TOKEN}
      CONCURRENT: ${CONCURRENT}
      TIMEOUT: ${TIMEOUT}
      QUEUED: ${QUEUED}
"""
ENV_DEFAULTS["chromium"] = {
    "IMAGE": "ghcr.io/browserless/chromium:latest",
    "CONTAINER_NAME": "chromium-service",
    "RESTART_POLICY": "unless-stopped",
    "BIND_IP": "127.0.0.1",
    "PORT": "3000",
    "TOKEN": "",
    "CONCURRENT": "5",
    "TIMEOUT": "60000",
    "QUEUED": "20",
}

TEMPLATES["playwright"] = """services:
  playwright:
    image: ${IMAGE}
    container_name: ${CONTAINER_NAME}
    restart: ${RESTART_POLICY}
    working_dir: ${WORKING_DIR}
    tty: true
    stdin_open: true
    shm_size: ${SHM_SIZE}
    volumes:
      - "${VOLUME}:/workspace"
    command: ["bash", "-lc", "${COMMAND}"]
"""
ENV_DEFAULTS["playwright"] = {
    "IMAGE": "mcr.microsoft.com/playwright:v1.52.0-noble",
    "CONTAINER_NAME": "playwright-service",
    "RESTART_POLICY": "unless-stopped",
    "WORKING_DIR": "/workspace",
    "SHM_SIZE": "2gb",
    "VOLUME": "./",
    "COMMAND": "sleep infinity",
}

TEMPLATES["headless-chromedriver"] = """services:
  chromedriver:
    image: ${IMAGE}
    container_name: ${CONTAINER_NAME}
    restart: ${RESTART_POLICY}
    shm_size: ${SHM_SIZE}
    ports:
      - "${BIND_IP}:${WEBDRIVER_PORT}:4444"
      - "${BIND_IP}:${VNC_PORT}:7900"
    environment:
      SE_NODE_MAX_SESSIONS: ${SE_NODE_MAX_SESSIONS}
      SE_VNC_NO_PASSWORD: ${SE_VNC_NO_PASSWORD}
"""
ENV_DEFAULTS["headless-chromedriver"] = {
    "IMAGE": "selenium/standalone-chrome:latest",
    "CONTAINER_NAME": "headless-chromedriver",
    "RESTART_POLICY": "unless-stopped",
    "SHM_SIZE": "2gb",
    "BIND_IP": "127.0.0.1",
    "WEBDRIVER_PORT": "4444",
    "VNC_PORT": "7900",
    "SE_NODE_MAX_SESSIONS": "1",
    "SE_VNC_NO_PASSWORD": "1",
}

ALIASES = {
    "chrominum": "chromium",
    "chromedriver": "headless-chromedriver",
    "headless-chromdriver": "headless-chromedriver",
}

def _resolve_template(name):
    normalized = (name or "").strip().lower()
    mapped = ALIASES.get(normalized, normalized)
    if mapped in TEMPLATES:
        return mapped
    return None

def _parse_set_values(items):
    values = {}
    for item in items:
        if "=" not in item:
            raise click.ClickException(f"Invalid --set format: {item}, expected KEY=VALUE")
        key, value = item.split("=", 1)
        values[key.strip()] = value
    return values

def _render_env_example(template_name, overrides):
    data = dict(ENV_DEFAULTS[template_name])
    data.update(overrides)
    lines = [f"{k}={v}" for k, v in data.items()]
    return "\n".join(lines) + "\n"

@click.command(name="docker")
@click.argument("template", required=False)
@click.argument("output_dir", required=False)
@click.option("--interactive/--no-interactive", "-i/-I", default=True, help="Interactive by default when required args are missing.")
@click.option("--set", "set_values", multiple=True, help="Override env value, e.g. --set PORT=3100")
@click.option("--compose-name", default="docker-compose.yaml", show_default=True, help="Output compose file name.")
@click.option("--env-name", default=None, help="Output env example file name. Default: <template>.env.example")
@click.option("--force", is_flag=True, help="Overwrite existing files without confirm.")
def docker_cmd(template, output_dir, interactive, set_values, compose_name, env_name, force):
    selected_template = _resolve_template(template)
    selected_output_dir = output_dir

    need_prompt = interactive and (not selected_template or not selected_output_dir)
    if need_prompt:
        if not is_interactive_available():
            click.echo("Missing required arguments and interactive mode is unavailable in current terminal.", err=True)
            click.echo("Usage: chattool docker <chromium|playwright|headless-chromedriver> <output_dir>", err=True)
            raise click.Abort()
        if not selected_template:
            selected_template = ask_select(
                "Select docker template:",
                choices=["chromium", "playwright", "headless-chromedriver"]
            )
            if selected_template == BACK_VALUE:
                return
        if not selected_output_dir:
            selected_output_dir = ask_path(
                "Output directory:",
                default=str(Path.cwd())
            )
            if selected_output_dir == BACK_VALUE:
                return

    if not selected_template or not selected_output_dir:
        click.echo("Usage: chattool docker <chromium|playwright|headless-chromedriver> <output_dir>", err=True)
        raise click.Abort()

    overrides = _parse_set_values(set_values)
    target_dir = Path(selected_output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    compose_file = target_dir / compose_name
    env_file = target_dir / (env_name or f"{selected_template}.env.example")

    if not force:
        if compose_file.exists() and not click.confirm(f"{compose_file} exists, overwrite?", default=False):
            click.echo("Cancelled.")
            return
        if env_file.exists() and not click.confirm(f"{env_file} exists, overwrite?", default=False):
            click.echo("Cancelled.")
            return

    compose_file.write_text(TEMPLATES[selected_template], encoding="utf-8")
    env_file.write_text(_render_env_example(selected_template, overrides), encoding="utf-8")
    click.echo(f"Generated compose: {compose_file}")
    click.echo(f"Generated env example: {env_file}")
    click.echo(f"Template: {selected_template}")
