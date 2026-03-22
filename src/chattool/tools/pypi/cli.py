from __future__ import annotations

import configparser
import os
from pathlib import Path
import subprocess

import click

from chattool.setup.interactive import (
    abort_if_force_without_tty,
    abort_if_missing_without_tty,
    normalize_interactive,
    resolve_interactive_mode,
)
from chattool.utils.tui import BACK_VALUE, ask_confirm, ask_text, is_interactive_available

from .main import (
    PyPICommandError,
    build_package,
    build_release_plan,
    check_distributions,
    check_repository_conflicts,
    collect_doctor_checks,
    doctor_has_failures,
    publish_distributions,
    read_project_metadata,
    release_package,
    resolve_dist_dir,
    scaffold_package,
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
    if not _prompt_confirm("Publish to the real PyPI index?", default=False):
        raise click.Abort()


def _load_pypirc() -> configparser.ConfigParser:
    parser = configparser.RawConfigParser()
    parser.read([Path("~/.pypirc").expanduser()])
    return parser


def _pypirc_credentials(repository: str, repository_url: str | None) -> tuple[str | None, str | None]:
    parser = _load_pypirc()
    candidate_sections = [repository]
    if repository_url:
        normalized_url = repository_url.rstrip("/")
        for section in parser.sections():
            configured_url = parser.get(section, "repository", fallback="").rstrip("/")
            if configured_url and configured_url == normalized_url:
                candidate_sections.insert(0, section)

    for section in candidate_sections:
        if not parser.has_section(section):
            continue
        username = _normalize_optional_text(parser.get(section, "username", fallback=None))
        password = _normalize_optional_text(parser.get(section, "password", fallback=None))
        if username and password:
            return username, password
    return None, None


def _resolve_twine_credentials(
    repository: str,
    repository_url: str | None,
    username: str | None,
    password: str | None,
) -> tuple[str | None, str | None, str | None]:
    explicit_username = _normalize_optional_text(username)
    explicit_password = _normalize_optional_text(password)
    if explicit_username and explicit_password:
        return explicit_username, explicit_password, "cli"

    config_username, config_password = _pypirc_credentials(repository, repository_url)
    if config_username and config_password:
        return config_username, config_password, ".pypirc"

    env_username = _normalize_optional_text(os.getenv("TWINE_USERNAME"))
    env_password = _normalize_optional_text(os.getenv("TWINE_PASSWORD"))
    if env_username and env_password:
        return env_username, env_password, "env"

    return explicit_username or env_username, explicit_password or env_password, None


def _maybe_prompt_credentials(
    repository: str,
    repository_url: str | None,
    username: str | None,
    password: str | None,
    interactive,
) -> tuple[str | None, str | None]:
    interactive = normalize_interactive(interactive)
    can_prompt = is_interactive_available()
    force_interactive = interactive is True
    abort_if_force_without_tty(force_interactive, can_prompt, "Usage: chattool pypi publish [-i|-I]")

    resolved_username, resolved_password, source = _resolve_twine_credentials(
        repository,
        repository_url,
        username,
        password,
    )
    if source == ".pypirc" and interactive is not True:
        return None, None
    if resolved_username and resolved_password:
        return resolved_username, resolved_password

    if interactive is True:
        username = _prompt_text_value("twine username", default=resolved_username or "__token__")
        password = _prompt_password_value("twine password", current_value=resolved_password)
        return username, password

    if interactive is None and can_prompt and source is None:
        if _prompt_confirm("Prompt for Twine credentials now?", default=False):
            username = _prompt_text_value("twine username", default=resolved_username or "__token__")
            password = _prompt_password_value("twine password", current_value=resolved_password)
            return username, password

    return resolved_username, resolved_password


def _print_files(files: list[Path], title: str) -> None:
    click.echo(title)
    for path in files:
        click.echo(f"- {path}")


def _raise_click_error(exc: Exception) -> None:
    raise click.ClickException(str(exc)) from exc


def _git_config_default(key: str) -> str | None:
    result = subprocess.run(
        ["git", "config", "--get", key],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _mask_secret(value: str | None) -> str:
    if not value:
        return ""
    value = str(value)
    if len(value) <= 4:
        return "*" * len(value)
    if len(value) <= 8:
        return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
    return f"{value[:3]}{'*' * (len(value) - 7)}{value[-4:]}"


def _prompt_text_value(label: str, default: str | None = None) -> str:
    answer = ask_text(label, default=default or "")
    if answer == BACK_VALUE:
        raise click.Abort()
    return answer.strip()


def _prompt_password_value(label: str, current_value: str | None = None) -> str | None:
    prompt_label = label
    if current_value:
        prompt_label = f"{prompt_label} (current: {_mask_secret(current_value)}, enter to keep)"
    answer = ask_text(prompt_label, password=True)
    if answer == BACK_VALUE:
        raise click.Abort()
    answer = answer.strip()
    if answer:
        return answer
    return current_value


def _prompt_confirm(label: str, *, default: bool) -> bool:
    answer = ask_confirm(label, default=default)
    if answer == BACK_VALUE:
        raise click.Abort()
    return bool(answer)


def _prompt_required_value(label: str, default: str | None = None, error_message: str | None = None) -> str:
    value = _prompt_text_value(label, default=default)
    if value:
        return value
    raise click.ClickException(error_message or f"{label} cannot be empty.")


def _prompt_path_value(label: str, default: str | None = None, error_message: str | None = None) -> Path:
    return Path(_prompt_required_value(label, default=default, error_message=error_message))


def _prompt_choice_value(label: str, choices: tuple[str, ...], default: str) -> str:
    value = _prompt_required_value(label, default=default)
    if value in choices:
        return value
    raise click.ClickException(f"{label} must be one of: {', '.join(choices)}.")


def _resolve_project_inputs(
    *,
    command_name: str,
    usage: str,
    project_dir: Path,
    dist_dir: Path | None,
    interactive,
    auto_prompt_condition: bool = False,
    start_message: str,
) -> tuple[Path, Path, object]:
    interactive, can_prompt, force_interactive, _, need_prompt = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=auto_prompt_condition,
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    if need_prompt:
        click.echo(start_message)
        project_dir = _prompt_path_value(
            "project_dir",
            default=str(project_dir),
            error_message="project_dir cannot be empty.",
        )
        dist_default = str(dist_dir) if dist_dir else str(resolve_dist_dir(project_dir, None))
        dist_dir = _prompt_path_value(
            "dist_dir",
            default=dist_default,
            error_message="dist_dir cannot be empty.",
        )

    resolved_project_dir = project_dir.resolve()
    resolved_dist_dir = resolve_dist_dir(
        resolved_project_dir,
        dist_dir.resolve() if dist_dir else None,
    )
    return resolved_project_dir, resolved_dist_dir, interactive


def _default_build_target(sdist: bool, wheel: bool) -> str:
    if sdist and not wheel:
        return "sdist"
    if wheel and not sdist:
        return "wheel"
    return "both"


def _resolve_build_inputs(
    *,
    project_dir: Path,
    dist_dir: Path | None,
    interactive,
    clean: bool,
    sdist: bool,
    wheel: bool,
) -> tuple[Path, Path, bool, bool, bool]:
    usage = (
        "Usage: chattool pypi build [--project-dir PATH] [--dist-dir PATH] "
        "[--wheel] [--sdist] [--clean/--no-clean] [-i|-I]"
    )
    project_dir, dist_dir, _ = _resolve_project_inputs(
        command_name="build",
        usage=usage,
        project_dir=project_dir,
        dist_dir=dist_dir,
        interactive=interactive,
        start_message="Starting interactive package build...",
    )
    if normalize_interactive(interactive) is True:
        build_target = _prompt_choice_value(
            "build_target",
            choices=("both", "sdist", "wheel"),
            default=_default_build_target(sdist, wheel),
        )
        clean = _prompt_confirm("clean old dist artifacts?", default=clean)
        sdist = build_target == "sdist"
        wheel = build_target == "wheel"
    return project_dir, dist_dir, clean, sdist, wheel


def _resolve_check_inputs(
    *,
    project_dir: Path,
    dist_dir: Path | None,
    interactive,
    strict: bool,
 ) -> tuple[Path, Path, bool]:
    usage = (
        "Usage: chattool pypi check [--project-dir PATH] [--dist-dir PATH] "
        "[--strict] [-i|-I]"
    )
    project_dir, dist_dir, _ = _resolve_project_inputs(
        command_name="check",
        usage=usage,
        project_dir=project_dir,
        dist_dir=dist_dir,
        interactive=interactive,
        start_message="Starting interactive package check...",
    )
    if normalize_interactive(interactive) is True:
        strict = _prompt_confirm("strict twine check?", default=strict)
    return project_dir, dist_dir, strict


def _resolve_probe_inputs(
    *,
    project_dir: Path,
    interactive,
    repository: str,
    repository_url: str | None,
    package_name: str | None,
    version: str | None,
) -> tuple[Path, str, str | None, str | None, str | None]:
    usage = (
        "Usage: chattool pypi probe [--project-dir PATH] [--repository testpypi|pypi] "
        "[--repository-url URL] [--name TEXT] [--version TEXT] [-i|-I]"
    )
    interactive, can_prompt, force_interactive, _, need_prompt = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=False,
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    resolved_project_dir = project_dir.resolve()
    if normalize_interactive(interactive) is True or need_prompt:
        click.echo("Starting interactive package probe...")
        resolved_project_dir = _prompt_path_value(
            "project_dir",
            default=str(resolved_project_dir),
            error_message="project_dir cannot be empty.",
        ).resolve()
        repository = _prompt_choice_value(
            "repository",
            choices=("testpypi", "pypi"),
            default=repository,
        )
        repository_url = _normalize_optional_text(
            _prompt_text_value("repository_url (optional)", default=repository_url or "")
        )
        package_name = _normalize_optional_text(
            _prompt_text_value("package_name override (optional)", default=package_name or "")
        )
        version = _normalize_optional_text(
            _prompt_text_value("version override (optional)", default=version or "")
        )

    return resolved_project_dir, repository, repository_url, package_name, version


def _resolve_publish_inputs(
    *,
    project_dir: Path,
    dist_dir: Path | None,
    interactive,
    repository: str,
    repository_url: str | None,
    skip_existing: bool,
    yes: bool,
    username: str | None,
    password: str | None,
    command_name: str,
    dry_run: bool = False,
) -> tuple[Path, Path, str, str | None, bool, bool, str | None, str | None, object]:
    usage = (
        f"Usage: chattool pypi {command_name} [--project-dir PATH] [--dist-dir PATH] "
        "[--repository testpypi|pypi] [--repository-url URL] [--skip-existing] "
        "[--username TEXT] [--password TEXT] [--yes] [-i|-I]"
    )
    project_dir, dist_dir, interactive = _resolve_project_inputs(
        command_name=command_name,
        usage=usage,
        project_dir=project_dir,
        dist_dir=dist_dir,
        interactive=interactive,
        start_message=f"Starting interactive package {command_name}...",
    )
    interactive_mode = normalize_interactive(interactive)
    resolved_username, resolved_password, credential_source = _resolve_twine_credentials(
        repository,
        repository_url,
        username,
        password,
    )

    if interactive_mode is True:
        repository = _prompt_choice_value(
            "repository",
            choices=("testpypi", "pypi"),
            default=repository,
        )
        repository_url = _normalize_optional_text(
            _prompt_text_value("repository_url (optional)", default=repository_url or "")
        )
        skip_existing = _prompt_confirm("skip_existing", default=skip_existing)
        if not dry_run and repository == "pypi":
            yes = _prompt_confirm("Publish to the real PyPI index?", default=yes)
            if not yes:
                raise click.Abort()
        username = _normalize_optional_text(
            _prompt_text_value("twine username (optional)", default=resolved_username or "__token__")
        )
        password = _prompt_password_value("twine password (optional)", current_value=resolved_password)
    else:
        if credential_source in {"cli", "env"}:
            username = resolved_username
            password = resolved_password
        else:
            username = None
            password = None

    return (
        project_dir,
        dist_dir,
        repository,
        repository_url,
        skip_existing,
        yes,
        username,
        password,
        interactive,
    )


def _resolve_init_inputs(
    *,
    name: str | None,
    description: str | None,
    initial_version: str,
    requires_python: str,
    license_name: str,
    author: str | None,
    email: str | None,
    project_dir: Path | None,
    interactive,
) -> tuple[str, str | None, str, str, str, str | None, str | None, Path]:
    inferred_name = _normalize_optional_text(name)
    if not inferred_name and project_dir is not None and project_dir.name:
        inferred_name = project_dir.name

    missing_required = not inferred_name
    usage = "Usage: chattool pypi init [NAME] [--project-dir PATH] [--description TEXT] [--version TEXT] [--python SPEC] [--license TEXT] [--author TEXT] [--email TEXT] [-i|-I]"
    interactive, can_prompt, force_interactive, _, need_prompt = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=missing_required,
    )

    abort_if_force_without_tty(force_interactive, can_prompt, usage)
    abort_if_missing_without_tty(
        missing_required=missing_required,
        interactive=interactive,
        can_prompt=can_prompt,
        message="Missing required package name and no TTY is available for interactive prompts.",
        usage=usage,
    )

    default_name = inferred_name or ""
    default_project_dir = str(project_dir) if project_dir is not None else (default_name or "")
    default_description = description or (f"{default_name} package" if default_name else "")
    default_version = initial_version or "0.1.0"
    default_python = requires_python or ">=3.10"
    default_license = license_name or "MIT"
    default_author = author or _git_config_default("user.name") or ""
    default_email = email or _git_config_default("user.email") or ""

    if need_prompt:
        click.echo("Starting interactive package scaffold...")
        package_name = _prompt_required_value("Package name", default=default_name, error_message="Package name cannot be empty.")
        project_dir_text = _prompt_required_value(
            "project_dir",
            default=default_project_dir or package_name,
            error_message="project_dir cannot be empty.",
        )
        description_text = _prompt_required_value(
            "description",
            default=default_description or f"{package_name} package",
            error_message="description cannot be empty.",
        )
        version_text = _prompt_required_value("initial_version", default=default_version, error_message="initial_version cannot be empty.")
        requires_python_text = _prompt_required_value("requires_python", default=default_python, error_message="requires_python cannot be empty.")
        license_text = _prompt_required_value("license", default=default_license, error_message="license cannot be empty.")
        author_text = _prompt_text_value("author (optional)", default=default_author)
        email_text = _prompt_text_value("email (optional)", default=default_email)

        return (
            package_name,
            _normalize_optional_text(description_text),
            version_text or "0.1.0",
            requires_python_text or ">=3.10",
            license_text or "MIT",
            _normalize_optional_text(author_text),
            _normalize_optional_text(email_text),
            Path(project_dir_text),
        )

    package_name = inferred_name
    if not package_name:
        raise click.ClickException("Package name is required.")
    target_dir = project_dir or Path(package_name)
    return (
        package_name,
        _normalize_optional_text(description) or f"{package_name} package",
        initial_version or "0.1.0",
        requires_python or ">=3.10",
        license_name or "MIT",
        _normalize_optional_text(author),
        _normalize_optional_text(email),
        target_dir,
    )


@click.group(name="pypi")
def cli():
    """Python package build/check/publish helpers."""
    pass


@cli.command(name="init")
@click.argument("name", required=False)
@click.option("--email", default=None, help="Author email to record in pyproject.toml.")
@click.option("--author", default=None, help="Author name to record in pyproject.toml.")
@click.option("--license", "license_name", default="MIT", show_default=True, help="Project license label.")
@click.option("--version", "initial_version", default="0.1.0", show_default=True, help="Initial package version written to src/<module>/__init__.py.")
@click.option("--python", "requires_python", default=">=3.10", show_default=True, help="Supported Python version specifier.")
@click.option("--description", default=None, help="Project description.")
@click.option(
    "--project-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
    help="Target directory to create. Defaults to ./{name}.",
)
@_interactive_options
def init(
    name: str | None,
    description: str | None,
    initial_version: str,
    requires_python: str,
    license_name: str,
    author: str | None,
    email: str | None,
    project_dir: Path | None,
    interactive,
):
    """Scaffold a minimal src-layout Python package."""
    package_name, description, initial_version, requires_python, license_name, author, email, target_dir = _resolve_init_inputs(
        name=name,
        description=description,
        initial_version=initial_version,
        requires_python=requires_python,
        license_name=license_name,
        author=author,
        email=email,
        project_dir=project_dir,
        interactive=interactive,
    )
    target_dir = target_dir.resolve()
    try:
        result = scaffold_package(
            package_name=package_name,
            project_dir=target_dir,
            initial_version=initial_version,
            description=description,
            requires_python=requires_python,
            license_name=license_name,
            author=author,
            email=email,
        )
    except PyPICommandError as exc:
        _raise_click_error(exc)

    click.echo(f"Created Python package scaffold: {result.package_name}")
    click.echo(f"project_dir={result.project_dir}")
    click.echo(f"module_name={result.module_name}")
    _print_files(result.created_files, "Created files:")


@cli.command(name="doctor")
@_project_options
@_interactive_options
def doctor(project_dir: Path, dist_dir: Path | None, interactive):
    """Check pyproject metadata, package files, and packaging dependencies."""
    project_dir, dist_dir, _ = _resolve_project_inputs(
        command_name="doctor",
        usage="Usage: chattool pypi doctor [--project-dir PATH] [--dist-dir PATH] [-i|-I]",
        project_dir=project_dir,
        dist_dir=dist_dir,
        interactive=interactive,
        start_message="Starting interactive package doctor...",
    )
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
    project_dir, dist_dir, clean, sdist, wheel = _resolve_build_inputs(
        project_dir=project_dir,
        dist_dir=dist_dir,
        interactive=interactive,
        clean=clean,
        sdist=sdist,
        wheel=wheel,
    )
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
def check(
    project_dir: Path,
    dist_dir: Path | None,
    interactive,
    strict: bool,
):
    """Validate built distributions with twine check."""
    project_dir, dist_dir, strict = _resolve_check_inputs(
        project_dir=project_dir,
        dist_dir=dist_dir,
        interactive=interactive,
        strict=strict,
    )
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

@cli.command(name="probe")
@click.option("--version", "package_version", default=None, help="Override the version used for repository conflict checks.")
@click.option("--name", "package_name", default=None, help="Override the package name used for repository conflict checks.")
@click.option("--repository-url", default=None, help="Custom repository URL. Overrides --repository.")
@click.option(
    "--repository",
    type=click.Choice(["testpypi", "pypi"]),
    default="testpypi",
    show_default=True,
    help="Target repository name for availability checks.",
)
@click.option(
    "--project-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("."),
    show_default=True,
    help="Project directory containing pyproject.toml for default metadata lookup.",
)
@_interactive_options
def probe(
    project_dir: Path,
    interactive,
    repository: str,
    repository_url: str | None,
    package_name: str | None,
    package_version: str | None,
):
    """Check whether a package name/version is already taken on PyPI or TestPyPI."""
    project_dir, repository, repository_url, package_name, package_version = _resolve_probe_inputs(
        project_dir=project_dir,
        interactive=interactive,
        repository=repository,
        repository_url=repository_url,
        package_name=package_name,
        version=package_version,
    )
    try:
        metadata = read_project_metadata(project_dir)
    except PyPICommandError:
        metadata = None

    target_name = _normalize_optional_text(package_name) or (metadata.name if metadata else None)
    target_version = _normalize_optional_text(package_version) or (metadata.version if metadata else None)
    if not target_name:
        raise click.ClickException("Package name is required. Pass --name or provide a readable pyproject.toml.")

    try:
        repository_checks = check_repository_conflicts(
            target_name,
            target_version,
            repository=repository,
            repository_url=repository_url,
        )
    except PyPICommandError as exc:
        _raise_click_error(exc)

    for item in repository_checks:
        click.echo(f"[{item.status.upper()}] {item.label}: {item.detail}")
        if item.hint:
            click.echo(f"  hint: {item.hint}")
    if any(item.status == "fail" for item in repository_checks):
        raise click.ClickException("Repository conflict checks found blocking issues.")


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
    project_dir, dist_dir, repository, repository_url, skip_existing, yes, username, password, interactive = _resolve_publish_inputs(
        project_dir=project_dir,
        dist_dir=dist_dir,
        interactive=interactive,
        repository=repository,
        repository_url=repository_url,
        skip_existing=skip_existing,
        yes=yes,
        username=username,
        password=password,
        command_name="publish",
    )
    _resolve_publish_confirmation(repository, yes, interactive)
    if normalize_interactive(interactive) is not True:
        username, password = _maybe_prompt_credentials(repository, repository_url, username, password, interactive)
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
    project_dir, dist_dir, repository, repository_url, skip_existing, yes, username, password, interactive = _resolve_publish_inputs(
        project_dir=project_dir,
        dist_dir=dist_dir,
        interactive=interactive,
        repository=repository,
        repository_url=repository_url,
        skip_existing=skip_existing,
        yes=yes,
        username=username,
        password=password,
        command_name="release",
        dry_run=dry_run,
    )
    if normalize_interactive(interactive) is True:
        build_target = _prompt_choice_value(
            "build_target",
            choices=("both", "sdist", "wheel"),
            default=_default_build_target(sdist, wheel),
        )
        clean = _prompt_confirm("clean old dist artifacts?", default=clean)
        strict = _prompt_confirm("strict twine check?", default=strict)
        sdist = build_target == "sdist"
        wheel = build_target == "wheel"

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
    if normalize_interactive(interactive) is not True:
        username, password = _maybe_prompt_credentials(repository, repository_url, username, password, interactive)
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
