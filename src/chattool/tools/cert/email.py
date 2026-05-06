from __future__ import annotations

from pathlib import Path


def get_git_user_email(start_path: str | Path = ".") -> str | None:
    """Return git config user.email from the current repo, then global config."""

    try:
        from git import GitConfigParser, Repo
    except Exception:
        Repo = None
        GitConfigParser = None

    if Repo is not None:
        try:
            repo = Repo(str(start_path), search_parent_directories=True)
            with repo.config_reader() as reader:
                value = reader.get_value("user", "email")
                if value:
                    return str(value)
        except Exception:
            pass

    if GitConfigParser is not None:
        try:
            gitconfig = str(Path("~/.gitconfig").expanduser())
            with GitConfigParser([gitconfig], read_only=True) as reader:
                value = reader.get_value("user", "email")
                if value:
                    return str(value)
        except Exception:
            pass

    return _get_git_user_email_from_command()


def _get_git_user_email_from_command() -> str | None:
    try:
        import subprocess

        result = subprocess.run(
            ["git", "config", "user.email"],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    value = result.stdout.strip()
    return value or None


def resolve_cert_email(email: str | None = None) -> str | None:
    if email:
        return email
    return get_git_user_email()
