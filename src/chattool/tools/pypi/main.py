from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import textwrap

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


DEFAULT_DIST_DIRNAME = "dist"


class PyPICommandError(RuntimeError):
    """Raised when a package operation cannot be completed safely."""


@dataclass
class ProjectMetadata:
    name: str | None
    version: str | None
    version_source: str | None
    readme: str | None
    requires_python: str | None
    license_text: str | None
    dynamic_fields: list[str]


@dataclass
class DoctorCheck:
    label: str
    status: str
    detail: str
    hint: str | None = None


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass
class ScaffoldResult:
    project_dir: Path
    package_name: str
    module_name: str
    created_files: list[Path]


def resolve_dist_dir(project_dir: Path, dist_dir: Path | None = None) -> Path:
    if dist_dir is None:
        return project_dir / DEFAULT_DIST_DIRNAME
    return dist_dir


def normalize_module_name(package_name: str) -> str:
    normalized = package_name.strip().replace("-", "_").replace(" ", "_")
    parts = [char if (char.isalnum() or char == "_") else "_" for char in normalized]
    module_name = "".join(parts).strip("_").lower()
    while "__" in module_name:
        module_name = module_name.replace("__", "_")
    if not module_name:
        raise PyPICommandError("Package name must contain at least one valid letter or digit.")
    if module_name[0].isdigit():
        raise PyPICommandError("Module name cannot start with a digit.")
    return module_name


def _toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _ensure_empty_or_missing(project_dir: Path) -> None:
    if not project_dir.exists():
        return
    if not project_dir.is_dir():
        raise PyPICommandError(f"Target path exists and is not a directory: {project_dir}")
    if any(project_dir.iterdir()):
        raise PyPICommandError(f"Target directory is not empty: {project_dir}")


def _build_pyproject_content(
    package_name: str,
    module_name: str,
    description: str,
    requires_python: str,
    license_name: str,
    author: str | None,
    email: str | None,
) -> str:
    lines = [
        "[build-system]",
        'requires = ["setuptools>=61.0", "wheel"]',
        'build-backend = "setuptools.build_meta"',
        "",
        "[project]",
        f'name = "{_toml_escape(package_name)}"',
        'dynamic = ["version"]',
        f'description = "{_toml_escape(description)}"',
        'readme = "README.md"',
        f'requires-python = "{_toml_escape(requires_python)}"',
        f'license = "{_toml_escape(license_name)}"',
    ]
    if author and email:
        lines.append(f'authors = [{{name = "{_toml_escape(author)}", email = "{_toml_escape(email)}"}}]')
    elif author:
        lines.append(f'authors = [{{name = "{_toml_escape(author)}"}}]')
    elif email:
        lines.append(f'authors = [{{email = "{_toml_escape(email)}"}}]')
    lines.extend([
        f'keywords = ["{_toml_escape(module_name)}"]',
        'classifiers = [',
        '    "Programming Language :: Python :: 3",',
        '    "Operating System :: OS Independent",',
        ']',
        "",
        "[tool.setuptools.dynamic]",
        f'version = {{attr = "{module_name}.__version__"}}',
        "",
        "[tool.setuptools.packages.find]",
        'where = ["src"]',
        "",
        "[tool.setuptools]",
        "include-package-data = true",
        "",
    ])
    return "\n".join(lines)


def scaffold_package(
    package_name: str,
    project_dir: Path,
    *,
    description: str | None = None,
    requires_python: str = ">=3.10",
    license_name: str = "MIT",
    author: str | None = None,
    email: str | None = None,
) -> ScaffoldResult:
    package_name = package_name.strip()
    if not package_name:
        raise PyPICommandError("Package name is required.")

    module_name = normalize_module_name(package_name)
    project_dir = Path(project_dir)
    _ensure_empty_or_missing(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    description = description or f"{package_name} package"
    src_dir = project_dir / "src" / module_name
    tests_dir = project_dir / "tests"
    created_files: list[Path] = []

    src_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    file_map = {
        project_dir / "pyproject.toml": _build_pyproject_content(
            package_name=package_name,
            module_name=module_name,
            description=description,
            requires_python=requires_python,
            license_name=license_name,
            author=author,
            email=email,
        ),
        project_dir / "README.md": textwrap.dedent(f"""
            # {package_name}

            {description}

            ## Quick Start

            ```bash
            chattool pypi doctor --project-dir .
            chattool pypi build --project-dir .
            chattool pypi check --project-dir .
            ```
        """).strip() + "\n",
        project_dir / "LICENSE": f"{license_name}\n",
        project_dir / ".gitignore": textwrap.dedent("""
            __pycache__/
            .pytest_cache/
            .venv/
            build/
            dist/
            *.egg-info/
        """).strip() + "\n",
        src_dir / "__init__.py": textwrap.dedent(f'''
            """{package_name} package."""

            __all__ = ["__version__"]

            __version__ = "0.1.0"
        ''').strip() + "\n",
        tests_dir / "test_version.py": textwrap.dedent(f"""
            from {module_name} import __version__


            def test_version_present():
                assert __version__ == "0.1.0"
        """).strip() + "\n",
    }

    for path, content in file_map.items():
        path.write_text(content, encoding="utf-8")
        created_files.append(path)

    return ScaffoldResult(
        project_dir=project_dir,
        package_name=package_name,
        module_name=module_name,
        created_files=sorted(created_files),
    )


def _load_pyproject(project_dir: Path) -> dict:
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        raise PyPICommandError(f"pyproject.toml not found under {project_dir}")
    try:
        return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        raise PyPICommandError(f"Failed to parse {pyproject_path}: {exc}") from exc


def _extract_license_text(license_value) -> str | None:
    if isinstance(license_value, str):
        return license_value
    if isinstance(license_value, dict):
        if license_value.get("text"):
            return str(license_value["text"])
        if license_value.get("file"):
            return f"file:{license_value['file']}"
    return None


def _extract_readme_path(readme_value) -> str | None:
    if isinstance(readme_value, str):
        return readme_value
    if isinstance(readme_value, dict) and readme_value.get("file"):
        return str(readme_value["file"])
    return None


def _resolve_dynamic_version_source(pyproject: dict, dynamic_fields: list[str]) -> str | None:
    if "version" not in dynamic_fields:
        return None
    tool_data = pyproject.get("tool", {})
    setuptools_data = tool_data.get("setuptools", {}) if isinstance(tool_data, dict) else {}
    dynamic_data = setuptools_data.get("dynamic", {}) if isinstance(setuptools_data, dict) else {}
    version_data = dynamic_data.get("version") if isinstance(dynamic_data, dict) else None
    if isinstance(version_data, dict):
        if version_data.get("attr"):
            return f"dynamic via attr={version_data['attr']}"
        if version_data.get("file"):
            return f"dynamic via file={version_data['file']}"
    return "dynamic"


def read_project_metadata(project_dir: Path) -> ProjectMetadata:
    pyproject = _load_pyproject(project_dir)
    project_data = pyproject.get("project")
    if not isinstance(project_data, dict):
        raise PyPICommandError("Missing [project] table in pyproject.toml")

    dynamic_fields = [
        field for field in project_data.get("dynamic", [])
        if isinstance(field, str)
    ]
    version = project_data.get("version")
    version_source = None
    if not version:
        version_source = _resolve_dynamic_version_source(pyproject, dynamic_fields)

    return ProjectMetadata(
        name=project_data.get("name"),
        version=version if isinstance(version, str) else None,
        version_source=version_source,
        readme=_extract_readme_path(project_data.get("readme")),
        requires_python=project_data.get("requires-python"),
        license_text=_extract_license_text(project_data.get("license")),
        dynamic_fields=dynamic_fields,
    )


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _find_license_file(project_dir: Path) -> Path | None:
    for candidate in ("LICENSE", "LICENSE.txt", "LICENSE.md"):
        path = project_dir / candidate
        if path.exists():
            return path
    return None


def collect_doctor_checks(project_dir: Path, dist_dir: Path | None = None) -> list[DoctorCheck]:
    project_dir = Path(project_dir)
    dist_dir = resolve_dist_dir(project_dir, dist_dir)
    pyproject_path = project_dir / "pyproject.toml"

    checks: list[DoctorCheck] = []
    if not pyproject_path.exists():
        return [
            DoctorCheck(
                label="pyproject.toml",
                status="fail",
                detail=f"missing: {pyproject_path}",
                hint="Create pyproject.toml before using chattool pypi.",
            )
        ]

    checks.append(DoctorCheck("pyproject.toml", "ok", f"found: {pyproject_path.name}"))

    try:
        metadata = read_project_metadata(project_dir)
    except PyPICommandError as exc:
        checks.append(DoctorCheck("project metadata", "fail", str(exc)))
        return checks

    checks.append(DoctorCheck(
        "project.name",
        "ok" if metadata.name else "fail",
        metadata.name or "missing [project].name",
    ))
    if metadata.version:
        version_detail = metadata.version
        status = "ok"
    elif metadata.version_source:
        version_detail = metadata.version_source
        status = "ok"
    else:
        version_detail = "missing version or dynamic version configuration"
        status = "fail"
    checks.append(DoctorCheck("project.version", status, version_detail))
    checks.append(DoctorCheck(
        "project.readme",
        "ok" if metadata.readme else "fail",
        metadata.readme or "missing [project].readme",
    ))
    checks.append(DoctorCheck(
        "project.requires-python",
        "ok" if metadata.requires_python else "fail",
        metadata.requires_python or "missing [project].requires-python",
    ))
    checks.append(DoctorCheck(
        "project.license",
        "ok" if metadata.license_text else "fail",
        metadata.license_text or "missing [project].license",
    ))

    if metadata.readme:
        readme_path = project_dir / metadata.readme
        checks.append(DoctorCheck(
            "README file",
            "ok" if readme_path.exists() else "fail",
            str(readme_path.relative_to(project_dir)) if readme_path.exists() else f"missing: {metadata.readme}",
        ))

    license_path = _find_license_file(project_dir)
    build_available = _module_available("build")
    twine_available = _module_available("twine")

    checks.append(DoctorCheck(
        "LICENSE file",
        "ok" if license_path else "fail",
        license_path.name if license_path else "missing LICENSE / LICENSE.txt / LICENSE.md",
    ))
    checks.append(DoctorCheck(
        "build module",
        "ok" if build_available else "fail",
        "installed" if build_available else "python -m build unavailable",
        hint="Install with `pip install build` or `pip install \"chattool[pypi]\"`.",
    ))
    checks.append(DoctorCheck(
        "twine module",
        "ok" if twine_available else "fail",
        "installed" if twine_available else "python -m twine unavailable",
        hint="Install with `pip install twine` or `pip install \"chattool[pypi]\"`.",
    ))

    existing_artifacts = find_distributions(dist_dir)
    if existing_artifacts:
        checks.append(DoctorCheck(
            "dist artifacts",
            "warn",
            f"{len(existing_artifacts)} existing file(s) under {dist_dir}",
            hint="Use `chattool pypi build --clean` to replace old build artifacts.",
        ))
    else:
        checks.append(DoctorCheck("dist artifacts", "ok", f"no existing artifacts under {dist_dir}"))
    return checks


def doctor_has_failures(checks: list[DoctorCheck]) -> bool:
    return any(check.status == "fail" for check in checks)


def find_distributions(dist_dir: Path) -> list[Path]:
    dist_dir = Path(dist_dir)
    if not dist_dir.exists():
        return []
    found: list[Path] = []
    for pattern in ("*.whl", "*.tar.gz", "*.zip"):
        found.extend(dist_dir.glob(pattern))
    return sorted(set(path.resolve() for path in found))


def _clean_dist_dir(dist_dir: Path) -> None:
    if not dist_dir.exists():
        return
    for path in dist_dir.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()


def run_command(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> CommandResult:
    process = subprocess.run(
        args,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        args=list(args),
        returncode=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def _ensure_success(result: CommandResult, action: str) -> CommandResult:
    if result.returncode == 0:
        return result
    detail = result.stderr.strip() or result.stdout.strip() or "no output"
    raise PyPICommandError(f"{action} failed: {detail}")


def build_package(
    project_dir: Path,
    dist_dir: Path | None = None,
    *,
    clean: bool = True,
    sdist: bool = False,
    wheel: bool = False,
    runner=run_command,
) -> tuple[CommandResult, list[Path]]:
    project_dir = Path(project_dir)
    dist_dir = resolve_dist_dir(project_dir, dist_dir)
    if not (project_dir / "pyproject.toml").exists():
        raise PyPICommandError(f"pyproject.toml not found under {project_dir}")

    if clean:
        _clean_dist_dir(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    args = [sys.executable, "-m", "build", "--outdir", str(dist_dir)]
    if sdist and not wheel:
        args.append("--sdist")
    elif wheel and not sdist:
        args.append("--wheel")

    result = _ensure_success(runner(args, project_dir), "Build")
    files = find_distributions(dist_dir)
    if not files:
        raise PyPICommandError(f"Build completed but no distributions were found under {dist_dir}")
    return result, files


def check_distributions(
    project_dir: Path,
    dist_dir: Path | None = None,
    *,
    strict: bool = False,
    runner=run_command,
) -> tuple[CommandResult, list[Path]]:
    project_dir = Path(project_dir)
    dist_dir = resolve_dist_dir(project_dir, dist_dir)
    files = find_distributions(dist_dir)
    if not files:
        raise PyPICommandError(
            f"No distributions found under {dist_dir}. Run `chattool pypi build` first."
        )

    args = [sys.executable, "-m", "twine", "check"]
    if strict:
        args.append("--strict")
    args.extend(str(path) for path in files)
    result = _ensure_success(runner(args, project_dir), "Twine check")
    return result, files


def _build_twine_env(username: str | None, password: str | None) -> dict[str, str]:
    env = os.environ.copy()
    if username is not None:
        env["TWINE_USERNAME"] = username
    if password is not None:
        env["TWINE_PASSWORD"] = password
    return env


def publish_distributions(
    project_dir: Path,
    dist_dir: Path | None = None,
    *,
    repository: str = "testpypi",
    repository_url: str | None = None,
    skip_existing: bool = False,
    username: str | None = None,
    password: str | None = None,
    non_interactive: bool = True,
    runner=run_command,
) -> tuple[CommandResult, list[Path]]:
    project_dir = Path(project_dir)
    dist_dir = resolve_dist_dir(project_dir, dist_dir)
    files = find_distributions(dist_dir)
    if not files:
        raise PyPICommandError(
            f"No distributions found under {dist_dir}. Run `chattool pypi build` first."
        )

    args = [sys.executable, "-m", "twine", "upload"]
    if repository_url:
        args.extend(["--repository-url", repository_url])
    else:
        args.extend(["--repository", repository])
    if skip_existing:
        args.append("--skip-existing")
    if non_interactive:
        args.append("--non-interactive")
    args.extend(str(path) for path in files)
    env = _build_twine_env(username, password)
    result = _ensure_success(runner(args, project_dir, env=env), "Twine upload")
    return result, files


def build_release_plan(
    project_dir: Path,
    dist_dir: Path | None = None,
    *,
    repository: str = "testpypi",
    repository_url: str | None = None,
    skip_existing: bool = False,
) -> list[str]:
    project_dir = Path(project_dir)
    dist_dir = resolve_dist_dir(project_dir, dist_dir)
    target = repository_url or repository
    return [
        f"project_dir={project_dir}",
        f"dist_dir={dist_dir}",
        "step=build",
        "step=check",
        f"step=publish target={target}",
        f"skip_existing={'yes' if skip_existing else 'no'}",
    ]


def release_package(
    project_dir: Path,
    dist_dir: Path | None = None,
    *,
    clean: bool = True,
    sdist: bool = False,
    wheel: bool = False,
    strict: bool = False,
    repository: str = "testpypi",
    repository_url: str | None = None,
    skip_existing: bool = False,
    username: str | None = None,
    password: str | None = None,
    non_interactive: bool = True,
    runner=run_command,
) -> dict[str, object]:
    build_result, build_files = build_package(
        project_dir,
        dist_dir,
        clean=clean,
        sdist=sdist,
        wheel=wheel,
        runner=runner,
    )
    check_result, checked_files = check_distributions(
        project_dir,
        dist_dir,
        strict=strict,
        runner=runner,
    )
    publish_result, published_files = publish_distributions(
        project_dir,
        dist_dir,
        repository=repository,
        repository_url=repository_url,
        skip_existing=skip_existing,
        username=username,
        password=password,
        non_interactive=non_interactive,
        runner=runner,
    )
    return {
        "build_result": build_result,
        "check_result": check_result,
        "publish_result": publish_result,
        "files": published_files or checked_files or build_files,
    }
