from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def append_token(url: str, token: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if "token" in query:
        return url
    query["token"] = [token]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def ensure_path(url: str, suffix: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path.endswith(suffix):
        return url
    if not path.endswith("/"):
        path = path + "/"
    new_path = path.rstrip("/") + suffix
    return urlunparse(parsed._replace(path=new_path))
