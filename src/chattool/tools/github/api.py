from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse
import subprocess
from typing import Optional

import click

from chattool.const import CHATTOOL_ENV_DIR
from chattool.config.github import GitHubConfig


def get_client(
    token: Optional[str],
    require_token: bool = False,
    credential_path: Optional[str] = None,
):
    from github import Github, Auth

    token = resolve_token(token, credential_path=credential_path)
    if require_token and not token:
        raise click.ClickException(
            "Missing token. Pass --token or configure a GitHub credential for the current repository."
        )
    if not token:
        click.secho(
            "Warning: no token provided; GitHub API rate limits may apply.", fg="yellow"
        )
        return Github()
    return Github(auth=Auth.Token(token))


def resolve_repo(repo: Optional[str]) -> str:
    if repo:
        normalized = repo.strip()
        if not normalized:
            raise click.ClickException("Repo must be in owner/name form.")
        return normalized
    resolved_repo, _ = resolve_repo_from_git_remote()
    return resolved_repo


def resolve_token(
    token: Optional[str], credential_path: Optional[str] = None
) -> Optional[str]:
    if token:
        return token
    return (
        read_github_token_from_credentials(credential_path)
        or GitHubConfig.GITHUB_ACCESS_TOKEN.value
    )


def resolve_repo_from_git_remote() -> tuple[str, str]:
    try:
        remotes_result = subprocess.run(
            ["git", "remote"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(
            "Current directory is not a git repository with any configured remote."
        ) from exc

    remote_names = [
        name.strip()
        for name in (remotes_result.stdout or "").splitlines()
        if name.strip()
    ]
    if not remote_names:
        raise click.ClickException(
            "Current directory is not a git repository with any configured remote."
        )

    ordered_remotes = ["origin", *[name for name in remote_names if name != "origin"]]
    checked_remotes = []
    for remote_name in ordered_remotes:
        if remote_name in checked_remotes:
            continue
        checked_remotes.append(remote_name)
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", remote_name],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            continue

        remote_url = (result.stdout or "").strip()
        parsed = parse_github_repo_from_remote(remote_url)
        if parsed:
            return parsed

    raise click.ClickException(
        "Current repository does not have a recognizable GitHub remote."
    )


def parse_github_repo_from_remote(remote_url: str) -> Optional[tuple[str, str]]:
    url = (remote_url or "").strip()
    if not url:
        return None

    prefixes = [
        "https://github.com/",
        "http://github.com/",
        "git@github.com:",
        "ssh://git@github.com/",
    ]
    for prefix in prefixes:
        if url.startswith(prefix):
            path = url[len(prefix) :]
            normalized_path = path[:-4] if path.endswith(".git") else path
            parts = [part for part in path.split("/") if part]
            if len(parts) >= 2:
                normalized_parts = [part for part in normalized_path.split("/") if part]
                return f"{normalized_parts[0]}/{normalized_parts[1]}", path
    return None


def read_github_token_from_credentials(
    credential_path: Optional[str] = None,
) -> Optional[str]:
    for store_path in _credential_store_candidates():
        if not store_path.exists():
            continue
        token = _read_token_from_store(store_path, credential_path)
        if token:
            return token
    return None


def _credential_store_candidates() -> list[Path]:
    return [Path.home() / ".git-credential", Path.home() / ".git-credentials"]


def _read_token_from_store(
    store_path: Path, credential_path: Optional[str]
) -> Optional[str]:
    exact_match = None
    host_match = None

    for raw_line in store_path.read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parsed = _parse_credential_url(line)
        if not parsed:
            continue
        host, path, password = parsed
        if host != "github.com" or not password:
            continue
        if credential_path and path == credential_path:
            exact_match = password
            break
        if host_match is None:
            host_match = password

    return exact_match or host_match


def _parse_credential_url(url: str) -> Optional[tuple[str, str, str]]:
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.hostname or not parsed.password:
        return None
    path = parsed.path.lstrip("/")
    return parsed.hostname, unquote(path), unquote(parsed.password)


def configure_github_https_token(path: str, token: str) -> None:
    try:
        subprocess.run(
            ["git", "config", "--global", "credential.helper", "store"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "--global", "credential.useHttpPath", "true"],
            check=True,
            capture_output=True,
            text=True,
        )
        credential_input = (
            "protocol=https\n"
            "host=github.com\n"
            f"path={path}\n"
            "username=x-access-token\n"
            f"password={token}\n\n"
        )
        subprocess.run(
            ["git", "credential", "approve"],
            input=credential_input,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise click.ClickException(
            f"Failed to configure GitHub token for {path}: {stderr or 'git credential command failed'}"
        ) from exc


def save_github_token_to_env(token: str) -> None:
    env_file = GitHubConfig.get_active_env_file(CHATTOOL_ENV_DIR)
    env_file.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8").splitlines()

    replaced = False
    rendered: list[str] = []
    for line in lines:
        if line.startswith("GITHUB_ACCESS_TOKEN="):
            rendered.append(f"GITHUB_ACCESS_TOKEN='{token}'")
            replaced = True
        else:
            rendered.append(line)

    if not replaced:
        if rendered and rendered[-1] != "":
            rendered.append("")
        rendered.append(f"GITHUB_ACCESS_TOKEN='{token}'")

    env_file.write_text("\n".join(rendered).rstrip() + "\n", encoding="utf-8")


def github_api_get_json(
    repo: str, path: str, token: Optional[str], params: Optional[dict] = None
) -> dict:
    response = github_api_request(repo, path, token, params=params)
    try:
        return response.json()
    except ValueError as exc:
        raise click.ClickException(
            f"GitHub API returned non-JSON response for {path}"
        ) from exc


def github_api_get_text(
    repo: str, path: str, token: Optional[str], params: Optional[dict] = None
) -> str:
    response = github_api_request(repo, path, token, params=params)
    return response.text


def github_api_request(
    repo: str, path: str, token: Optional[str], params: Optional[dict] = None
):
    import requests

    owner, name = split_repo(repo)
    url = f"https://api.github.com/repos/{owner}/{name}{path}"
    try:
        response = requests.get(
            url,
            headers=github_api_headers(token),
            params=params,
            timeout=30,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        raise click.ClickException(
            f"GitHub API request failed for {path}: {exc}"
        ) from exc
    if response.ok:
        return response

    detail = response.text.strip()
    try:
        payload = response.json()
        if isinstance(payload, dict) and payload.get("message"):
            detail = payload["message"]
    except ValueError:
        pass
    raise click.ClickException(
        f"GitHub API error ({response.status_code}) for {path}: {detail}"
    )


def github_api_headers(token: Optional[str]) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "chattool-gh",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def split_repo(repo: str) -> tuple[str, str]:
    parts = repo.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise click.ClickException("Repo must be in owner/name form.")
    return parts[0], parts[1]
