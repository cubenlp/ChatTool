from __future__ import annotations

from pathlib import Path

import click

from .main import (
    PyPICommandError,
    build_package,
    check_distributions,
    check_repository_conflicts,
    read_project_metadata,
    resolve_dist_dir,
    scaffold_package,
    upload_distributions,
)


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


def _print_files(files: list[Path], title: str) -> None:
    click.echo(title)
    for path in files:
        click.echo(f"- {path}")


def _raise_click_error(exc: Exception) -> None:
    raise click.ClickException(str(exc)) from exc


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


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
) -> tuple[str, str | None, str, str, str, str | None, str | None, Path]:
    package_name = _normalize_optional_text(name)
    if not package_name and project_dir is not None and project_dir.name:
        package_name = project_dir.name
    if not package_name:
        raise click.ClickException("Package name is required. Pass NAME or --project-dir.")

    target_dir = (project_dir or Path(package_name)).resolve()
    return (
        package_name,
        _normalize_optional_text(description) or f"{package_name} package",
        initial_version or "0.1.0",
        requires_python or ">=3.9",
        license_name or "MIT",
        _normalize_optional_text(author),
        _normalize_optional_text(email),
        target_dir,
    )


def _resolve_project_dir(project_dir: Path) -> Path:
    return project_dir.resolve()


def _resolve_project_and_dist_dirs(project_dir: Path, dist_dir: Path | None) -> tuple[Path, Path]:
    resolved_project_dir = _resolve_project_dir(project_dir)
    resolved_dist_dir = resolve_dist_dir(
        resolved_project_dir,
        dist_dir.resolve() if dist_dir else None,
    )
    return resolved_project_dir, resolved_dist_dir


@click.group(name="pypi")
def cli():
    """Python package scaffold/build/check/upload helpers."""
    pass


@cli.command(name="init")
@click.argument("name", required=False)
@click.option("--email", default=None, help="Author email to record in pyproject.toml.")
@click.option("--author", default=None, help="Author name to record in pyproject.toml.")
@click.option("--license", "license_name", default="MIT", show_default=True, help="Project license label.")
@click.option("--version", "initial_version", default="0.1.0", show_default=True, help="Initial package version written to src/<module>/__init__.py.")
@click.option("--python", "requires_python", default=">=3.9", show_default=True, help="Supported Python version specifier.")
@click.option("--description", default=None, help="Project description.")
@click.option(
    "--project-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
    help="Target directory to create. Defaults to ./{name}.",
)
def init(
    name: str | None,
    description: str | None,
    initial_version: str,
    requires_python: str,
    license_name: str,
    author: str | None,
    email: str | None,
    project_dir: Path | None,
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
    )
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


@cli.command(name="build")
@click.option("--wheel", is_flag=True, help="Build wheel only.")
@click.option("--sdist", is_flag=True, help="Build source distribution only.")
@click.option("--clean/--no-clean", default=True, show_default=True, help="Clean old files in dist directory first.")
@_project_options
def build(project_dir: Path, dist_dir: Path | None, clean: bool, sdist: bool, wheel: bool):
    """Build wheel and/or source distribution with python -m build."""
    project_dir, dist_dir = _resolve_project_and_dist_dirs(project_dir, dist_dir)
    click.echo(f"Building distributions from {project_dir} into {dist_dir}...")
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
def check(project_dir: Path, dist_dir: Path | None, strict: bool):
    """Validate built distributions with twine check."""
    project_dir, dist_dir = _resolve_project_and_dist_dirs(project_dir, dist_dir)
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


@cli.command(name="upload")
@click.option("--skip-existing", is_flag=True, help="Pass --skip-existing to twine upload.")
@_project_options
def upload(project_dir: Path, dist_dir: Path | None, skip_existing: bool):
    """Upload built distributions with the default twine upload behavior."""
    project_dir, dist_dir = _resolve_project_and_dist_dirs(project_dir, dist_dir)
    click.echo(f"Uploading distributions from {dist_dir} with `twine upload`...")
    try:
        result, files = upload_distributions(
            project_dir,
            dist_dir,
            skip_existing=skip_existing,
        )
    except PyPICommandError as exc:
        _raise_click_error(exc)
    _echo_result_output(result)
    _print_files(files, "Uploaded distributions:")


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
def probe(
    project_dir: Path,
    repository: str,
    repository_url: str | None,
    package_name: str | None,
    package_version: str | None,
):
    """Check whether a package name/version is already taken on PyPI or TestPyPI."""
    project_dir = _resolve_project_dir(project_dir)
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
