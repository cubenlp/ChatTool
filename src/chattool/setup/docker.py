from __future__ import annotations

import getpass
import os
import shutil
import subprocess

import click

from chattool.interaction import (
    BACK_VALUE,
    abort_if_force_without_tty,
    ask_confirm,
    resolve_interactive_mode,
)
from chattool.utils.custom_logger import setup_logger

logger = setup_logger("setup_docker")
DOCKER_COMPOSE_VERSION = "v2.22.0"


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True)


def _ensure_success(result: subprocess.CompletedProcess, step_name: str) -> None:
    if result.returncode == 0:
        return
    detail = (result.stderr or result.stdout or "").strip()
    logger.error(f"{step_name} failed: {detail}")
    click.echo(f"{step_name} failed.", err=True)
    if detail:
        click.echo(detail, err=True)
    raise click.Abort()


def _get_user_name() -> str:
    return os.getenv("USER") or getpass.getuser()


def _docker_version() -> str:
    if not shutil.which("docker"):
        return ""
    result = _run(["docker", "--version"])
    return result.stdout.strip() if result.returncode == 0 else ""


def _docker_compose_version() -> str:
    if shutil.which("docker-compose"):
        result = _run(["docker-compose", "--version"])
        if result.returncode == 0:
            return result.stdout.strip()
    if shutil.which("docker"):
        result = _run(["docker", "compose", "version"])
        if result.returncode == 0:
            return result.stdout.strip()
    return ""


def _user_in_docker_group(user_name: str) -> bool:
    result = _run(["groups", user_name])
    return result.returncode == 0 and "docker" in result.stdout.split()


def _maybe_run_command(
    allow_sudo: bool,
    interactive: bool | None,
    can_prompt: bool,
    prompt: str,
    command: list[str],
    label: str,
) -> None:
    command_text = " ".join(command)
    if not allow_sudo:
        click.echo(f"Suggested: {command_text}")
        return
    if interactive is not False and can_prompt:
        confirmed = ask_confirm(
            f"{prompt}\n`--sudo` is enabled. Run now: `{command_text}`?",
            default=False,
        )
        if confirmed == BACK_VALUE:
            raise click.Abort()
        if confirmed:
            _ensure_success(_run(command), label)
            click.echo(f"{label} completed.")
            return
    click.echo(f"Suggested: {command_text}")


def setup_docker(interactive=None, use_sudo=False):
    usage = "Usage: chattool setup docker [--sudo] [-i|-I]"
    interactive, can_prompt, force_interactive, _, _ = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=True,
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    logger.info("Start docker setup")
    user_name = _get_user_name()

    docker_version = _docker_version()
    if docker_version:
        click.echo(f"Docker already installed: {docker_version}")
    else:
        click.echo("Docker not found.")
        _maybe_run_command(
            use_sudo,
            interactive,
            can_prompt,
            "Docker is not installed.",
            ["sudo", "apt", "install", "docker.io", "-y"],
            "Install Docker",
        )

    compose_version = _docker_compose_version()
    if compose_version:
        click.echo(f"Docker Compose already installed: {compose_version}")
    else:
        click.echo("Docker Compose not found.")
        click.echo(
            "Suggested download command: "
            f"curl -L https://github.com/docker/compose/releases/download/{DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m) -o ~/downloads/docker-compose"
        )
        _maybe_run_command(
            use_sudo,
            interactive,
            can_prompt,
            f"Docker Compose {DOCKER_COMPOSE_VERSION} is not installed.",
            [
                "sudo",
                "cp",
                os.path.expanduser("~/downloads/docker-compose"),
                "/usr/bin/",
            ],
            "Install Docker Compose",
        )

    if _user_in_docker_group(user_name):
        click.echo(f"User {user_name} is already in docker group.")
    else:
        click.echo(f"User {user_name} is not in docker group.")
        _maybe_run_command(
            use_sudo,
            interactive,
            can_prompt,
            f"Docker group access is not enabled for {user_name}.",
            ["sudo", "usermod", "-aG", "docker", user_name],
            "Add user to docker group",
        )
        click.echo("Re-login may be required after group changes.")

    click.echo("Docker setup check completed.")
