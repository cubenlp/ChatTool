from __future__ import annotations

from dataclasses import dataclass

import click


@dataclass(frozen=True)
class TemplateField:
    key: str
    label: str
    default: str = ""


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    category: str
    title: str
    description: str
    content: str
    fields: tuple[TemplateField, ...]
    prompt_fields: tuple[str, ...]


CATEGORY_LABELS = {
    "proxy": "Proxy / 转发",
    "site": "Site / 站点",
}


TEMPLATE_SPECS = {
    "proxy-pass": TemplateSpec(
        name="proxy-pass",
        category="proxy",
        title="Basic reverse proxy",
        description="Single server block with a standard proxy_pass upstream.",
        content="""server {
    listen __LISTEN__;
    server_name __SERVER_NAME__;

    location __LOCATION__ {
        proxy_pass __PROXY_PASS__;

        proxy_set_header Host __HOST_HEADER__;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
""",
        fields=(
            TemplateField("LISTEN", "listen", "80"),
            TemplateField("SERVER_NAME", "server_name", "app.example.com"),
            TemplateField("LOCATION", "location", "/"),
            TemplateField("PROXY_PASS", "proxy_pass", "http://127.0.0.1:8080"),
            TemplateField("HOST_HEADER", "Host header", "$host"),
        ),
        prompt_fields=("SERVER_NAME", "PROXY_PASS"),
    ),
    "proxy-pass-https": TemplateSpec(
        name="proxy-pass-https",
        category="proxy",
        title="HTTPS reverse proxy",
        description="Port 80 redirects to 443, then 443 proxies to an upstream.",
        content="""server {
    listen __REDIRECT_LISTEN__;
    server_name __SERVER_NAME__;
    return __REDIRECT_CODE__ https://$host$request_uri;
}

server {
    listen __LISTEN__;
    server_name __SERVER_NAME__;
    ssl_certificate __SSL_CERTIFICATE__;
    ssl_certificate_key __SSL_CERTIFICATE_KEY__;
    client_max_body_size __CLIENT_MAX_BODY_SIZE__;

    location __LOCATION__ {
        proxy_pass __PROXY_PASS__;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host __HOST_HEADER__;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
""",
        fields=(
            TemplateField("REDIRECT_LISTEN", "redirect listen", "80"),
            TemplateField("LISTEN", "https listen", "443 ssl"),
            TemplateField("SERVER_NAME", "server_name", "app.example.com"),
            TemplateField("REDIRECT_CODE", "redirect code", "301"),
            TemplateField(
                "SSL_CERTIFICATE",
                "ssl_certificate",
                "/etc/letsencrypt/live/example/fullchain.pem",
            ),
            TemplateField(
                "SSL_CERTIFICATE_KEY",
                "ssl_certificate_key",
                "/etc/letsencrypt/live/example/privkey.pem",
            ),
            TemplateField("CLIENT_MAX_BODY_SIZE", "client_max_body_size", "100M"),
            TemplateField("LOCATION", "location", "/"),
            TemplateField("PROXY_PASS", "proxy_pass", "http://127.0.0.1:8080"),
            TemplateField("HOST_HEADER", "Host header", "$host"),
        ),
        prompt_fields=(
            "SERVER_NAME",
            "PROXY_PASS",
            "SSL_CERTIFICATE",
            "SSL_CERTIFICATE_KEY",
        ),
    ),
    "websocket-proxy": TemplateSpec(
        name="websocket-proxy",
        category="proxy",
        title="WebSocket proxy",
        description="Reverse proxy with Upgrade/Connection headers for WebSocket-style upstreams.",
        content="""server {
    listen __LISTEN__;
    server_name __SERVER_NAME__;

    location __LOCATION__ {
        proxy_pass __PROXY_PASS__;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host __HOST_HEADER__;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout __PROXY_READ_TIMEOUT__;
    }
}
""",
        fields=(
            TemplateField("LISTEN", "listen", "80"),
            TemplateField("SERVER_NAME", "server_name", "ws.example.com"),
            TemplateField("LOCATION", "location", "/"),
            TemplateField("PROXY_PASS", "proxy_pass", "http://127.0.0.1:3000"),
            TemplateField("HOST_HEADER", "Host header", "$host"),
            TemplateField("PROXY_READ_TIMEOUT", "proxy_read_timeout", "86400s"),
        ),
        prompt_fields=("SERVER_NAME", "PROXY_PASS"),
    ),
    "static-root": TemplateSpec(
        name="static-root",
        category="site",
        title="Static root / NAS directory",
        description="Serve a local directory or static site root.",
        content="""server {
    listen __LISTEN__;
    server_name __SERVER_NAME__;

    ssl_certificate __SSL_CERTIFICATE__;
    ssl_certificate_key __SSL_CERTIFICATE_KEY__;

    location __LOCATION__ {
        root __ROOT_DIR__;
        autoindex on;
        charset utf-8;
    }
}
""",
        fields=(
            TemplateField("LISTEN", "listen", "443 ssl"),
            TemplateField("SERVER_NAME", "server_name", "share.example.com"),
            TemplateField(
                "SSL_CERTIFICATE",
                "ssl_certificate",
                "/etc/letsencrypt/live/example/fullchain.pem",
            ),
            TemplateField(
                "SSL_CERTIFICATE_KEY",
                "ssl_certificate_key",
                "/etc/letsencrypt/live/example/privkey.pem",
            ),
            TemplateField("LOCATION", "location", "/"),
            TemplateField("ROOT_DIR", "root directory", "/storage/nas"),
        ),
        prompt_fields=(
            "SERVER_NAME",
            "ROOT_DIR",
            "SSL_CERTIFICATE",
            "SSL_CERTIFICATE_KEY",
        ),
    ),
    "redirect": TemplateSpec(
        name="redirect",
        category="site",
        title="HTTP redirect",
        description="Redirect one or more hostnames to another URL pattern.",
        content="""server {
    listen __LISTEN__;
    server_name __SERVER_NAME__;
    return __REDIRECT_CODE__ __TARGET__;
}
""",
        fields=(
            TemplateField("LISTEN", "listen", "80"),
            TemplateField(
                "SERVER_NAME",
                "server_name",
                "example.com www.example.com",
            ),
            TemplateField("REDIRECT_CODE", "redirect code", "301"),
            TemplateField("TARGET", "redirect target", "https://$host$request_uri"),
        ),
        prompt_fields=("SERVER_NAME", "TARGET"),
    ),
}

ALIASES = {
    "proxy": "proxy-pass",
    "https-proxy": "proxy-pass-https",
    "tls-proxy": "proxy-pass-https",
    "ws": "websocket-proxy",
    "nas": "static-root",
    "static": "static-root",
    "site": "static-root",
    "redirect-https": "redirect",
}

USAGE = (
    "chattool nginx [proxy-pass|proxy-pass-https|websocket-proxy|static-root|redirect] "
    "[output_file] [--set KEY=VALUE] [-i|-I]"
)


def resolve_template(name: str | None) -> str | None:
    normalized = (name or "").strip().lower()
    mapped = ALIASES.get(normalized, normalized)
    if mapped in TEMPLATE_SPECS:
        return mapped
    return None


def parse_set_values(items: tuple[str, ...]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise click.ClickException(
                f"Invalid --set format: {item}, expected KEY=VALUE"
            )
        key, value = item.split("=", 1)
        values[key.strip().upper()] = value
    return values


def build_template_values(
    template_name: str, overrides: dict[str, str]
) -> dict[str, str]:
    spec = TEMPLATE_SPECS[template_name]
    values = {field.key: field.default for field in spec.fields}
    values.update(overrides)
    return values


def render_template(template_name: str, overrides: dict[str, str] | None = None) -> str:
    values = build_template_values(template_name, overrides or {})
    content = TEMPLATE_SPECS[template_name].content
    for key, value in values.items():
        content = content.replace(f"__{key}__", str(value))
    return content


def list_templates_by_category() -> list[tuple[str, list[TemplateSpec]]]:
    ordered_categories = ["proxy", "site"]
    grouped: list[tuple[str, list[TemplateSpec]]] = []
    for category in ordered_categories:
        specs = [spec for spec in TEMPLATE_SPECS.values() if spec.category == category]
        if specs:
            grouped.append((category, specs))
    return grouped
