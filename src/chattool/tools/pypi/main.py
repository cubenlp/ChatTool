from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import textwrap
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

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


@dataclass
class RepositoryCheck:
    label: str
    status: str
    detail: str
    hint: str | None = None


def _extract_project_snippets(payload: dict | None) -> list[RepositoryCheck]:
    if not isinstance(payload, dict):
        return []
    info = payload.get("info")
    if not isinstance(info, dict):
        return []

    snippets: list[RepositoryCheck] = []
    version = info.get("version")
    if isinstance(version, str) and version.strip():
        snippets.append(RepositoryCheck("latest version", "info", version.strip()))

    summary = info.get("summary")
    if isinstance(summary, str) and summary.strip():
        snippets.append(RepositoryCheck("summary", "info", summary.strip()))

    author = info.get("author")
    if isinstance(author, str) and author.strip():
        snippets.append(RepositoryCheck("author", "info", author.strip()))

    author_email = info.get("author_email")
    if isinstance(author_email, str) and author_email.strip():
        snippets.append(RepositoryCheck("author email", "info", author_email.strip()))

    requires_python = info.get("requires_python")
    if isinstance(requires_python, str) and requires_python.strip():
        snippets.append(
            RepositoryCheck("requires python", "info", requires_python.strip())
        )

    project_url = info.get("project_url") or info.get("home_page")
    if isinstance(project_url, str) and project_url.strip():
        snippets.append(RepositoryCheck("project url", "info", project_url.strip()))

    return snippets


def _normalized_project_name(name: str) -> str:
    return name.strip().lower().replace("_", "-").replace(".", "-")


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
        raise PyPICommandError(
            "Package name must contain at least one valid letter or digit."
        )
    if module_name[0].isdigit():
        raise PyPICommandError("Module name cannot start with a digit.")
    return module_name


def _toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _ensure_empty_or_missing(project_dir: Path) -> None:
    if not project_dir.exists():
        return
    if not project_dir.is_dir():
        raise PyPICommandError(
            f"Target path exists and is not a directory: {project_dir}"
        )
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
        lines.append(
            f'authors = [{{name = "{_toml_escape(author)}", email = "{_toml_escape(email)}"}}]'
        )
    elif author:
        lines.append(f'authors = [{{name = "{_toml_escape(author)}"}}]')
    elif email:
        lines.append(f'authors = [{{email = "{_toml_escape(email)}"}}]')
    lines.extend(
        [
            f'keywords = ["{_toml_escape(module_name)}"]',
            "classifiers = [",
            '    "Programming Language :: Python :: 3",',
            '    "Operating System :: OS Independent",',
            "]",
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
        ]
    )
    return "\n".join(lines)


def _build_cli_style_readme(package_name: str, description: str) -> str:
    return (
        textwrap.dedent(
            f"""
            # {package_name}

            {description}

            ## Quick Start

            ```bash
            python -m pytest -q
            python -m build
            ```

            ## Layout

            - `src/`: package source code
            - `tests/`: historical/basic test area
            - `cli-tests/`: real CLI tests, doc-first
            - `mock-cli-tests/`: mock/fake CLI tests, doc-first
            - `docs/`: long-lived project docs

            ## Development Notes

            See `DEVELOP.md` and `setup.md` before expanding the scaffold.
            """
        ).strip()
        + "\n"
    )


def _build_cli_style_develop_md() -> str:
    return (
        textwrap.dedent(
            """
            # Development Guide

            ## CLI Rules

            - Missing required args should auto-enter interactive mode when recoverable.
            - `-i` forces interactive mode; `-I` disables prompting and must fail fast.
            - Prompt defaults must match actual execution defaults.
            - Sensitive values must stay masked in prompts and summaries.
            - Prefer lazy imports in CLI wiring and keep implementation imports local when possible.

            ## Docs and Tests

            - Use doc-first CLI testing.
            - Put real CLI coverage under `cli-tests/`.
            - Put mock/fake CLI coverage under `mock-cli-tests/`.
            - Keep `README.md`, `docs/`, and `CHANGELOG.md` in sync with user-facing changes.

            ## Automation

            - Keep automation small and reviewable.
            - Prefer commands that can run in CI without interactive prompts.
            - Ensure generated defaults are safe for local development.
            """
        ).strip()
        + "\n"
    )


def _build_cli_style_setup_md(package_name: str) -> str:
    return (
        textwrap.dedent(
            f"""
            # Setup

            This scaffold was generated from the `cli-style` template.

            Use this file as the first handoff note for the model or developer after initialization.

            ## Initial Checklist

            1. Confirm the project goal and target users.
            2. Update `README.md` to match the actual package purpose.
            3. Decide whether this package needs a CLI, library API, or both.
            4. Add or remove folders from the scaffold as needed.
            5. Expand tests using the doc-first conventions in `cli-tests/` and `mock-cli-tests/`.

            ## Suggested Next Edits

            - Replace the placeholder description for `{package_name}`.
            - Add concrete commands or module structure.
            - Add CI steps that match the real project needs.
            """
        ).strip()
        + "\n"
    )


def _build_cli_style_changelog() -> str:
    return "# Changelog\n\n## [Unreleased]\n\n### Added\n\n### Changed\n\n### Fixed\n"


def _build_cli_style_docs_index(package_name: str) -> str:
    return f"# Docs\n\nLong-lived documentation for `{package_name}` lives here.\n"


def _build_cli_style_agends_md() -> str:
    return (
        textwrap.dedent(
            """
            # Agent Notes

            ## Development Expectations

            - Keep changes minimal and reviewable.
            - Prefer doc-first CLI tests.
            - Sync docs and changelog with user-facing behavior.
            - Use interactive prompts only when arguments are missing and recoverable.
            """
        ).strip()
        + "\n"
    )


def scaffold_package(
    package_name: str,
    project_dir: Path,
    *,
    initial_version: str = "0.1.0",
    description: str | None = None,
    requires_python: str = ">=3.9",
    license_name: str = "MIT",
    author: str | None = None,
    email: str | None = None,
    template: str = "default",
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
            chattool pypi build --project-dir .
            chattool pypi check --project-dir .
            chattool pypi upload --project-dir .
            ```
        """).strip()
        + "\n",
        project_dir / "LICENSE": f"{license_name}\n",
        project_dir / ".gitignore": textwrap.dedent("""
            __pycache__/
            .pytest_cache/
            .venv/
            build/
            dist/
            *.egg-info/
        """).strip()
        + "\n",
        src_dir / "__init__.py": textwrap.dedent(f'''
            """{package_name} package."""

            __all__ = ["__version__"]

            __version__ = "{initial_version}"
        ''').strip()
        + "\n",
        tests_dir / "conftest.py": textwrap.dedent("""
            from pathlib import Path
            import sys


            ROOT = Path(__file__).resolve().parents[1]
            SRC = ROOT / "src"
            if str(SRC) not in sys.path:
                sys.path.insert(0, str(SRC))
        """).strip()
        + "\n",
        tests_dir / "test_version.py": textwrap.dedent(f"""
            from {module_name} import __version__


            def test_version_present():
                assert __version__ == "{initial_version}"
        """).strip()
        + "\n",
    }

    if template == "cli-style":
        (project_dir / "cli-tests").mkdir(parents=True, exist_ok=True)
        (project_dir / "mock-cli-tests").mkdir(parents=True, exist_ok=True)
        (project_dir / "docs").mkdir(parents=True, exist_ok=True)
        file_map.update(
            {
                project_dir / "README.md": _build_cli_style_readme(
                    package_name, description
                ),
                project_dir / "DEVELOP.md": _build_cli_style_develop_md(),
                project_dir / "setup.md": _build_cli_style_setup_md(package_name),
                project_dir / "CHANGELOG.md": _build_cli_style_changelog(),
                project_dir / "AGENTS.md": _build_cli_style_agends_md(),
                project_dir / "docs" / "README.md": _build_cli_style_docs_index(
                    package_name
                ),
                project_dir
                / "cli-tests"
                / "README.md": "# CLI Tests\n\nReal CLI tests live here.\n",
                project_dir
                / "mock-cli-tests"
                / "README.md": "# Mock CLI Tests\n\nMock/fake CLI tests live here.\n",
            }
        )

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


def _resolve_dynamic_version_source(
    pyproject: dict, dynamic_fields: list[str]
) -> str | None:
    if "version" not in dynamic_fields:
        return None
    tool_data = pyproject.get("tool", {})
    setuptools_data = (
        tool_data.get("setuptools", {}) if isinstance(tool_data, dict) else {}
    )
    dynamic_data = (
        setuptools_data.get("dynamic", {}) if isinstance(setuptools_data, dict) else {}
    )
    version_data = (
        dynamic_data.get("version") if isinstance(dynamic_data, dict) else None
    )
    if isinstance(version_data, dict):
        if version_data.get("attr"):
            return f"dynamic via attr={version_data['attr']}"
        if version_data.get("file"):
            return f"dynamic via file={version_data['file']}"
    return "dynamic"


def _load_attr_version(project_dir: Path, attr_path: str) -> str | None:
    module_path, _, attribute = attr_path.rpartition(".")
    if not module_path or not attribute:
        return None
    relative_parts = module_path.split(".")
    candidate_files = []
    for base_dir in (project_dir / "src", project_dir):
        candidate_files.append(base_dir.joinpath(*relative_parts, "__init__.py"))
        candidate_files.append(base_dir.joinpath(*relative_parts).with_suffix(".py"))

    for candidate in candidate_files:
        if not candidate.exists():
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                f"_chattool_pypi_dynamic_{candidate.stem}_{abs(hash(candidate))}",
                candidate,
            )
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            value = getattr(module, attribute, None)
        except Exception:  # pragma: no cover
            continue
        if value is not None:
            return str(value)
    return None


def _load_file_version(project_dir: Path, relative_path: str) -> str | None:
    target = project_dir / relative_path
    if not target.exists():
        return None
    content = target.read_text(encoding="utf-8").strip()
    return content or None


def _resolve_dynamic_version_value(
    project_dir: Path, pyproject: dict, dynamic_fields: list[str]
) -> str | None:
    if "version" not in dynamic_fields:
        return None
    tool_data = pyproject.get("tool", {})
    setuptools_data = (
        tool_data.get("setuptools", {}) if isinstance(tool_data, dict) else {}
    )
    dynamic_data = (
        setuptools_data.get("dynamic", {}) if isinstance(setuptools_data, dict) else {}
    )
    version_data = (
        dynamic_data.get("version") if isinstance(dynamic_data, dict) else None
    )
    if isinstance(version_data, dict):
        attr_path = version_data.get("attr")
        if isinstance(attr_path, str):
            return _load_attr_version(project_dir, attr_path)
        file_path = version_data.get("file")
        if isinstance(file_path, str):
            return _load_file_version(project_dir, file_path)
    return None


def read_project_metadata(project_dir: Path) -> ProjectMetadata:
    pyproject = _load_pyproject(project_dir)
    project_data = pyproject.get("project")
    if not isinstance(project_data, dict):
        raise PyPICommandError("Missing [project] table in pyproject.toml")

    dynamic_fields = [
        field for field in project_data.get("dynamic", []) if isinstance(field, str)
    ]
    version = project_data.get("version")
    version_source = None
    if not version:
        version_source = _resolve_dynamic_version_source(pyproject, dynamic_fields)
        version = _resolve_dynamic_version_value(project_dir, pyproject, dynamic_fields)

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


def collect_doctor_checks(
    project_dir: Path, dist_dir: Path | None = None
) -> list[DoctorCheck]:
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

    checks.append(
        DoctorCheck(
            "project.name",
            "ok" if metadata.name else "fail",
            metadata.name or "missing [project].name",
        )
    )
    if metadata.version:
        version_detail = metadata.version
        if metadata.version_source:
            version_detail = f"{metadata.version} ({metadata.version_source})"
        status = "ok"
    elif metadata.version_source:
        version_detail = metadata.version_source
        status = "ok"
    else:
        version_detail = "missing version or dynamic version configuration"
        status = "fail"
    checks.append(DoctorCheck("project.version", status, version_detail))
    checks.append(
        DoctorCheck(
            "project.readme",
            "ok" if metadata.readme else "fail",
            metadata.readme or "missing [project].readme",
        )
    )
    checks.append(
        DoctorCheck(
            "project.requires-python",
            "ok" if metadata.requires_python else "fail",
            metadata.requires_python or "missing [project].requires-python",
        )
    )
    checks.append(
        DoctorCheck(
            "project.license",
            "ok" if metadata.license_text else "fail",
            metadata.license_text or "missing [project].license",
        )
    )

    if metadata.readme:
        readme_path = project_dir / metadata.readme
        checks.append(
            DoctorCheck(
                "README file",
                "ok" if readme_path.exists() else "fail",
                str(readme_path.relative_to(project_dir))
                if readme_path.exists()
                else f"missing: {metadata.readme}",
            )
        )

    license_path = _find_license_file(project_dir)
    build_available = _module_available("build")
    twine_available = _module_available("twine")

    checks.append(
        DoctorCheck(
            "LICENSE file",
            "ok" if license_path else "fail",
            license_path.name
            if license_path
            else "missing LICENSE / LICENSE.txt / LICENSE.md",
        )
    )
    checks.append(
        DoctorCheck(
            "build module",
            "ok" if build_available else "fail",
            "installed" if build_available else "python -m build unavailable",
            hint='Install with `pip install build` or `pip install "chattool[pypi]"`.',
        )
    )
    checks.append(
        DoctorCheck(
            "twine module",
            "ok" if twine_available else "fail",
            "installed" if twine_available else "python -m twine unavailable",
            hint='Install with `pip install twine` or `pip install "chattool[pypi]"`.',
        )
    )

    existing_artifacts = find_distributions(dist_dir)
    if existing_artifacts:
        checks.append(
            DoctorCheck(
                "dist artifacts",
                "warn",
                f"{len(existing_artifacts)} existing file(s) under {dist_dir}",
                hint="Use `chattool pypi build --clean` to replace old build artifacts.",
            )
        )
    else:
        checks.append(
            DoctorCheck(
                "dist artifacts", "ok", f"no existing artifacts under {dist_dir}"
            )
        )
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


def _repository_json_base(repository: str, repository_url: str | None = None) -> str:
    if repository_url:
        parsed = urllib_parse.urlparse(repository_url)
        host = parsed.netloc.lower()
        if host == "upload.pypi.org":
            return "https://pypi.org"
        if host == "test.pypi.org":
            return "https://test.pypi.org"
        return f"{parsed.scheme}://{parsed.netloc}"
    if repository == "pypi":
        return "https://pypi.org"
    return "https://test.pypi.org"


def _fetch_repository_json(url: str, timeout: float = 5.0) -> tuple[int, dict | None]:
    request = urllib_request.Request(
        url,
        headers={"Accept": "application/json"},
    )
    try:
        with urllib_request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload)
    except urllib_error.HTTPError as exc:
        if exc.code == 404:
            return 404, None
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise PyPICommandError(
            f"Repository query failed for {url}: HTTP {exc.code} {detail or exc.reason}"
        ) from exc
    except urllib_error.URLError as exc:
        raise PyPICommandError(
            f"Repository query failed for {url}: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise PyPICommandError(f"Repository query failed for {url}: timeout") from exc
    except json.JSONDecodeError as exc:
        raise PyPICommandError(
            f"Repository query returned invalid JSON for {url}: {exc}"
        ) from exc


def check_repository_conflicts(
    package_name: str,
    *,
    repository: str = "pypi",
    repository_url: str | None = None,
    timeout: float = 5.0,
    fetcher=_fetch_repository_json,
) -> list[RepositoryCheck]:
    package_name = package_name.strip()
    if not package_name:
        raise PyPICommandError(
            "Package name is required for repository conflict checks."
        )

    base_url = _repository_json_base(repository, repository_url)
    package_url = f"{base_url}/pypi/{urllib_parse.quote(package_name)}/json"
    package_status, payload = fetcher(package_url, timeout=timeout)
    target_label = repository_url or repository

    checks: list[RepositoryCheck] = []
    if package_status == 404:
        return [
            RepositoryCheck(
                label="package name",
                status="ok",
                detail=f"{package_name} is available on {target_label}",
                hint="Exact project-name check. This does not use PyPI search results.",
            ),
            RepositoryCheck(
                label="result",
                status="ok",
                detail=f"name is available on {target_label}",
                hint="Use this as a first-pass name check before publishing.",
            ),
        ]
    else:
        checks.append(
            RepositoryCheck(
                label="package name",
                status="fail",
                detail=f"{package_name} already exists on {target_label}",
                hint="Choose another package name for a new package. Only keep this name if you own the existing project.",
            )
        )
        checks.append(
            RepositoryCheck(
                label="result",
                status="fail",
                detail=f"blocked for a new package: {package_name} already exists on {target_label}",
                hint="Choose another package name unless you own the existing project.",
            )
        )
        checks.extend(_extract_project_snippets(payload))
    return checks


def _clean_dist_dir(dist_dir: Path) -> None:
    if not dist_dir.exists():
        return
    for path in dist_dir.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()


def run_command(
    args: list[str], cwd: Path, env: dict[str, str] | None = None
) -> CommandResult:
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
        raise PyPICommandError(
            f"Build completed but no distributions were found under {dist_dir}"
        )
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


def upload_distributions(
    project_dir: Path,
    dist_dir: Path | None = None,
    *,
    skip_existing: bool = False,
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
    if skip_existing:
        args.append("--skip-existing")
    args.extend(str(path) for path in files)
    result = _ensure_success(runner(args, project_dir), "Twine upload")
    return result, files
