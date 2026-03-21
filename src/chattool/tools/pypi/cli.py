from __future__ import annotations

import os
from pathlib import Path

import click

from chattool.setup.interactive import abort_if_force_without_tty, normalize_interactive
from chattool.utils.tui import is_interactive_available

from .main import (
    PyPICommandError,
    build_package,
    build_release_plan,
    check_distributions,
    collect_doctor_checks,
    doctor_has_failures,
    publish_distributions,
    release_package,
    resolve_dist_dir,
)


def _interactive_options(func):
    func = click.option(
        "-I",
        "--no-interactive",
        "interactive",
        flag_value=False,
        help="Disable interactive prompts; fail fast instead.",
    )(func)
    func = click.option(
        "-i",
        "--interactive",
        "interactive",
        flag_value=True,
        default=None,
        help="Force interactive prompts when confirmation or credentials are needed.",
    )(func)
    return func


def _project_options(func):
    func = click.option(
        "--dist-dir",
        type=click.Path(path_type=Path, file_okay=False),
        default=None,
        help="Distribution directory. Defaults to <project-dir>/dist.",
    )(func)
    func = click.option(
        "--project-dir",
        type=click.Path(path_type=Path, file_okay=False),
        default=Path("."),
        show_default=True,
        help="Project directory containing pyproject.toml.",
    )(func)
    return func


def _echo_result_output(result) -> None:
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if stdout:
        click.echo(stdout)
    if stderr:
        click.echo(stderr, err=True)


def _resolve_publish_confirmation(repository: str, yes: bool, interactive) -> None:
    if repository != "pypi" or yes:
        return
    interactive = normalize_interactive(interactive)
    can_prompt = is_interactive_available()
    force_interactive = interactive is True
    abort_if_force_without_tty(force_interactive, can_prompt, "Usage: chattool pypi publish --repository pypi --yes")
    if interactive is False or not can_prompt:
        raise click.ClickException("Publishing to `pypi` requires `--yes` or an interactive confirmation.")
    if not click.confirm("Publish to the real PyPI index?", default=False):
        raise click.Abort()


def _maybe_prompt_credentials(username: str | None, password: str | None, interactive) -> tuple[str | None, str | None]:
    interactive = normalize_interactive(interactive)
    can_prompt = is_interactive_available()
    force_interactive = interactive is True
    abort_if_force_without_tty(force_interactive, can_prompt, "Usage: chattool pypi publish [-i|-I]")

    env_username = username or os.getenv("TWINE_USERNAME")
    env_password = password or os.getenv("TWINE_PASSWORD")
    if env_username and env_password:
        return env_username, env_password

    if interactive is True:
        username = env_username or click.prompt("Twine username", default="__token__")
        password = env_password or click.prompt("Twine password", hide_input=True)
        return username, password

    if interactive is None and can_prompt and not (env_username and env_password):
        if click.confirm("Prompt for Twine credentials now?", default=False):
            username = env_username or click.prompt("Twine username", default="__token__")
            password = env_password or click.prompt("Twine password", hide_input=True)
            return username, password

    return env_username, env_password


def _print_files(files: list[Path], title: str) -> None:
    click.echo(title)
    for path in files:
        click.echo(f"- {path}")


def _raise_click_error(exc: Exception) -> None:
    raise click.ClickException(str(exc)) from exc


@click.group(name="pypi")
def cli():
    """Python package build/check/publish helpers."""
    pass


@cli.command(name="doctor")
@_project_options
@_interactive_options
def doctor(project_dir: Path, dist_dir: Path | None, interactive):
    """Check pyproject metadata, package files, and packaging dependencies."""
    del interactive
    project_dir = project_dir.resolve()
    dist_dir = resolve_dist_dir(project_dir, dist_dir.resolve() if dist_dir else None)
    checks = collect_doctor_checks(project_dir, dist_dir)
    for check in checks:
        click.echo(f"[{check.status.upper()}] {check.label}: {check.detail}")
        if check.hint:
            click.echo(f"  hint: {check.hint}")
    if doctor_has_failures(checks):
        raise click.ClickException("PyPI doctor found failed checks.")
    click.echo("Doctor checks passed.")


@cli.command(name="build")
@click.option("--wheel", is_flag=True, help="Build wheel only.")
@click.option("--sdist", is_flag=True, help="Build source distribution only.")
@click.option("--clean/--no-clean", default=True, show_default=True, help="Clean old files in dist directory first.")
@_project_options
@_interactive_options
def build(project_dir: Path, dist_dir: Path | None, interactive, clean: bool, sdist: bool, wheel: bool):
    """Build wheel and/or source distribution with python -m build."""
    del interactive
    project_dir = project_dir.resolve()
    dist_dir = resolve_dist_dir(project_dir, dist_dir.resolve() if dist_dir else None)
    try:
        result, files = build_package(
            project_dir,
            dist_dir,
            clean=clean,
            sdist=sdist,
            wheel=wheel,
        )
    except PyPICommandError as exc:
        _raise_click_error(exc)
    _echo_result_output(result)
    _print_files(files, "Built distributions:")


@cli.command(name="check")
@click.option("--strict", is_flag=True, help="Fail on warnings reported by twine check.")
@_project_options
@_interactive_options
def check(project_dir: Path, dist_dir: Path | None, interactive, strict: bool):
    """Validate built distributions with twine check."""
    del interactive
    project_dir = project_dir.resolve()
    dist_dir = resolve_dist_dir(project_dir, dist_dir.resolve() if dist_dir else None)
    try:
        result, files = check_distributions(
            project_dir,
            dist_dir,
            strict=strict,
        )
    except PyPICommandError as exc:
        _raise_click_error(exc)
    _echo_result_output(result)
    _print_files(files, "Checked distributions:")


@cli.command(name="publish")
@click.option("--password", default=None, help="Twine password or token. Prefer env vars in automation.")
@click.option("--username", default=None, help="Twine username. Defaults to TWINE_USERNAME when present.")
@click.option("--yes", is_flag=True, help="Skip the confirmation prompt when publishing to PyPI.")
@click.option("--skip-existing", is_flag=True, help="Skip files that are already present on the target index.")
@click.option("--repository-url", default=None, help="Custom repository URL. Overrides --repository.")
@click.option(
    "--repository",
    type=click.Choice(["testpypi", "pypi"]),
    default="testpypi",
    show_default=True,
    help="Target repository name from ~/.pypirc.",
)
@_project_options
@_interactive_options
def publish(
    project_dir: Path,
    dist_dir: Path | None,
    interactive,
    repository: str,
    repository_url: str | None,
    skip_existing: bool,
    yes: bool,
    username: str | None,
    password: str | None,
):
    """Upload built distributions with twine upload."""
    project_dir = project_dir.resolve()
    dist_dir = resolve_dist_dir(project_dir, dist_dir.resolve() if dist_dir else None)
    _resolve_publish_confirmation(repository, yes, interactive)
    username, password = _maybe_prompt_credentials(username, password, interactive)
    try:
        result, files = publish_distributions(
            project_dir,
            dist_dir,
            repository=repository,
            repository_url=repository_url,
            skip_existing=skip_existing,
            username=username,
            password=password,
            non_interactive=interactive is not True,
        )
    except PyPICommandError as exc:
        _raise_click_error(exc)
    _echo_result_output(result)
    _print_files(files, "Published distributions:")


@cli.command(name="release")
@click.option("--dry-run", is_flag=True, help="Print the release plan without building or uploading.")
@click.option("--password", default=None, help="Twine password or token. Prefer env vars in automation.")
@click.option("--username", default=None, help="Twine username. Defaults to TWINE_USERNAME when present.")
@click.option("--yes", is_flag=True, help="Skip the confirmation prompt when publishing to PyPI.")
@click.option("--skip-existing", is_flag=True, help="Skip files that are already present on the target index.")
@click.option("--repository-url", default=None, help="Custom repository URL. Overrides --repository.")
@click.option(
    "--repository",
    type=click.Choice(["testpypi", "pypi"]),
    default="testpypi",
    show_default=True,
    help="Target repository name from ~/.pypirc.",
)
@click.option("--strict", is_flag=True, help="Fail on warnings reported by twine check.")
@click.option("--wheel", is_flag=True, help="Build wheel only.")
@click.option("--sdist", is_flag=True, help="Build source distribution only.")
@click.option("--clean/--no-clean", default=True, show_default=True, help="Clean old files in dist directory first.")
@_project_options
@_interactive_options
def release(
    project_dir: Path,
    dist_dir: Path | None,
    interactive,
    clean: bool,
    sdist: bool,
    wheel: bool,
    strict: bool,
    repository: str,
    repository_url: str | None,
    skip_existing: bool,
    yes: bool,
    username: str | None,
    password: str | None,
    dry_run: bool,
):
    """Run build -> check -> publish as one guarded flow."""
    project_dir = project_dir.resolve()
    dist_dir = resolve_dist_dir(project_dir, dist_dir.resolve() if dist_dir else None)
    click.echo("Release plan:")
    for item in build_release_plan(
        project_dir,
        dist_dir,
        repository=repository,
        repository_url=repository_url,
        skip_existing=skip_existing,
    ):
        click.echo(f"- {item}")

    if dry_run:
        click.echo("Dry run only; no commands executed.")
        return

    _resolve_publish_confirmation(repository, yes, interactive)
    username, password = _maybe_prompt_credentials(username, password, interactive)
    try:
        summary = release_package(
            project_dir,
            dist_dir,
            clean=clean,
            sdist=sdist,
            wheel=wheel,
            strict=strict,
            repository=repository,
            repository_url=repository_url,
            skip_existing=skip_existing,
            username=username,
            password=password,
            non_interactive=interactive is not True,
        )
    except PyPICommandError as exc:
        _raise_click_error(exc)

    _echo_result_output(summary["build_result"])
    _echo_result_output(summary["check_result"])
    _echo_result_output(summary["publish_result"])
    _print_files(summary["files"], "Released distributions:")
