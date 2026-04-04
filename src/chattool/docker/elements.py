import click


TEMPLATES = {
    "chromium": """services:
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
""",
    "playwright": """services:
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
""",
    "headless-chromedriver": """services:
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
""",
    "nas": """services:
  fileserver:
    image: ${IMAGE}
    container_name: ${CONTAINER_NAME}
    restart: ${RESTART_POLICY}
    volumes:
      - "${RESOURCE_DIR}:/web"
    ports:
      - "${BIND_IP}:${PORT}:8080"
    environment:
      URL_PREFIX: ${URL_PREFIX}
""",
}

ENV_DEFAULTS = {
    "chromium": {
        "IMAGE": "ghcr.io/browserless/chromium:latest",
        "CONTAINER_NAME": "chromium-service",
        "RESTART_POLICY": "unless-stopped",
        "BIND_IP": "127.0.0.1",
        "PORT": "3000",
        "TOKEN": "",
        "CONCURRENT": "5",
        "TIMEOUT": "60000",
        "QUEUED": "20",
    },
    "playwright": {
        "IMAGE": "mcr.microsoft.com/playwright:v1.52.0-noble",
        "CONTAINER_NAME": "playwright-service",
        "RESTART_POLICY": "unless-stopped",
        "WORKING_DIR": "/workspace",
        "SHM_SIZE": "2gb",
        "VOLUME": "./",
        "COMMAND": "sleep infinity",
    },
    "headless-chromedriver": {
        "IMAGE": "selenium/standalone-chrome:latest",
        "CONTAINER_NAME": "headless-chromedriver",
        "RESTART_POLICY": "unless-stopped",
        "SHM_SIZE": "2gb",
        "BIND_IP": "127.0.0.1",
        "WEBDRIVER_PORT": "4444",
        "VNC_PORT": "7900",
        "SE_NODE_MAX_SESSIONS": "1",
        "SE_VNC_NO_PASSWORD": "1",
    },
    "nas": {
        "IMAGE": "",
        "CONTAINER_NAME": "",
        "RESTART_POLICY": "",
        "RESOURCE_DIR": "",
        "BIND_IP": "",
        "PORT": "",
        "URL_PREFIX": "",
    },
}

ALIASES = {
    "chrominum": "chromium",
    "chromedriver": "headless-chromedriver",
    "headless-chromdriver": "headless-chromedriver",
    "fileserver": "nas",
}

USAGE = "chattool docker <chromium|playwright|headless-chromedriver|nas> <output_dir>"


def resolve_template(name):
    normalized = (name or "").strip().lower()
    mapped = ALIASES.get(normalized, normalized)
    if mapped in TEMPLATES:
        return mapped
    return None


def parse_set_values(items):
    values = {}
    for item in items:
        if "=" not in item:
            raise click.ClickException(
                f"Invalid --set format: {item}, expected KEY=VALUE"
            )
        key, value = item.split("=", 1)
        values[key.strip()] = value
    return values


def render_env_example(template_name, overrides):
    data = dict(ENV_DEFAULTS[template_name])
    data.update(overrides)
    lines = [f"{k}={v}" for k, v in data.items()]
    return "\n".join(lines) + "\n"
