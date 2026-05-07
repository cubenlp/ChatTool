from __future__ import annotations

from urllib.parse import urlparse
import subprocess
from typing import Optional, TypedDict

import click

from chattool.const import CHATARCH_ENV_DIR
from chattool.config import GitHubConfig

class CredentialQuery(TypedDict):
    protocol: str
    host: str
    path: str


class ResolvedToken(TypedDict):
    token: Optional[str]
    source: str


def get_client(
    token: Optional[str],
    require_token: bool = False,
    credential_path: Optional[CredentialQuery] = None,
):
    from github import Github, Auth

    token = resolve_token(token, credential_path=credential_path)
    if require_token and not token:
        raise click.ClickException(
            "Missing token. Pass --token or run `chattool gh set-token` inside the current repository to configure a repo-scoped GitHub credential."
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
    token: Optional[str],
    credential_path: Optional[CredentialQuery] = None,
    exact_only: bool = False,
) -> Optional[str]:
    return resolve_token_with_source(
        token, credential_path=credential_path, exact_only=exact_only
    )["token"]


def resolve_token_with_source(
    token: Optional[str],
    credential_path: Optional[CredentialQuery] = None,
    exact_only: bool = False,
) -> ResolvedToken:
    if token:
        return {"token": token, "source": "--token"}
    credential_token = read_github_token_from_git(
        credential_path, exact_only=exact_only
    )
    if credential_token:
        return {"token": credential_token, "source": "git credential"}
    credential_token = read_github_token_from_credentials(
        credential_path, exact_only=exact_only
    )
    if credential_token:
        return {"token": credential_token, "source": "credentials file"}
    if credential_path and exact_only:
        return {"token": None, "source": "none"}
    config_token = GitHubConfig.GITHUB_ACCESS_TOKEN.value
    if config_token:
        return {"token": config_token, "source": "GitHubConfig.GITHUB_ACCESS_TOKEN"}
    return {"token": None, "source": "none"}


def credential_path_from_repo(repo: str) -> dict[str, str]:
    normalized = repo.strip().removesuffix(".git")
    return {"protocol": "https", "host": "github.com", "path": normalized}


def resolve_repo_from_git_remote() -> tuple[str, dict[str, str]]:
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


def parse_github_repo_from_remote(remote_url: str) -> Optional[tuple[str, dict[str, str]]]:
    url = (remote_url or "").strip()
    if not url:
        return None

    if url.startswith(("https://", "http://")):
        parsed = urlparse(url)
        if parsed.hostname != "github.com":
            return None
        path = parsed.path.lstrip("/")
        normalized_path = path[:-4] if path.endswith(".git") else path
        parts = [part for part in normalized_path.split("/") if part]
        if len(parts) >= 2:
            return (
                f"{parts[0]}/{parts[1]}",
                {"protocol": parsed.scheme, "host": "github.com", "path": path},
            )

    if url.startswith("git@github.com:"):
        path = url[len("git@github.com:") :]
        normalized_path = path[:-4] if path.endswith(".git") else path
        parts = [part for part in normalized_path.split("/") if part]
        if len(parts) >= 2:
            return (
                f"{parts[0]}/{parts[1]}",
                {"protocol": "https", "host": "github.com", "path": path},
            )

    if url.startswith("ssh://git@github.com/"):
        path = url[len("ssh://git@github.com/") :]
        normalized_path = path[:-4] if path.endswith(".git") else path
        parts = [part for part in normalized_path.split("/") if part]
        if len(parts) >= 2:
            return (
                f"{parts[0]}/{parts[1]}",
                {"protocol": "https", "host": "github.com", "path": path},
            )
    return None


def read_github_token_from_credentials(
    credential_path: Optional[CredentialQuery] = None,
    exact_only: bool = False,
) -> Optional[str]:
    return None


def read_github_token_from_git(
    credential_path: Optional[CredentialQuery] = None,
    exact_only: bool = False,
) -> Optional[str]:
    if not credential_path:
        return None
    return _git_credential_fill(credential_path)


def _git_credential_fill(credential: CredentialQuery) -> Optional[str]:
    credential_input = (
        f"protocol={credential['protocol']}\n"
        f"host={credential['host']}\n"
        f"path={credential['path']}\n"
    )
    credential_input += "\n"
    try:
        result = subprocess.run(
            ["git", "credential", "fill"],
            input=credential_input,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    if values.get("host") != credential["host"]:
        return None
    return values.get("password") or None


def configure_github_https_token(credential: CredentialQuery, token: str) -> None:
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
            f"protocol={credential['protocol']}\n"
            f"host={credential['host']}\n"
            f"path={credential['path']}\n"
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
            f"Failed to configure GitHub token for {credential['path']}: {stderr or 'git credential command failed'}"
        ) from exc


def save_github_token_to_env(token: str) -> None:
    env_file = GitHubConfig.get_active_env_file(CHATARCH_ENV_DIR)
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
        f"GitHub API error ({response.status_code}) for {path}: {detail}. If this repository should use a dedicated token, run `chattool gh set-token` inside the repo to add a matching git credential entry."
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
