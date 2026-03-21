from pathlib import Path
import sys

import pytest

from chattool.tools.pypi.main import (
    PyPICommandError,
    build_package,
    check_distributions,
    collect_doctor_checks,
    normalize_module_name,
    publish_distributions,
    release_package,
    scaffold_package,
)


def _write_minimal_project(root: Path) -> None:
    (root / "pyproject.toml").write_text(
        """
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "demo-pkg"
version = "0.1.0"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")


def test_collect_doctor_checks_reports_dynamic_version(tmp_path):
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text(
        """
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "demo-pkg"
dynamic = ["version"]
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

[tool.setuptools.dynamic]
version = {attr = "demo.__version__"}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (project_dir / "README.md").write_text("# demo\n", encoding="utf-8")
    (project_dir / "LICENSE").write_text("MIT\n", encoding="utf-8")
    dist_dir = project_dir / "dist"
    dist_dir.mkdir()
    (dist_dir / "demo_pkg-0.1.0-py3-none-any.whl").write_text("wheel", encoding="utf-8")

    checks = collect_doctor_checks(project_dir, dist_dir)
    version_check = next(check for check in checks if check.label == "project.version")
    artifact_check = next(check for check in checks if check.label == "dist artifacts")

    assert version_check.status == "ok"
    assert version_check.detail == "dynamic via attr=demo.__version__"
    assert artifact_check.status == "warn"


def test_build_package_cleans_old_artifacts_and_returns_new_files(tmp_path):
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    dist_dir.mkdir()
    stale_file = dist_dir / "stale.whl"
    stale_file.write_text("old", encoding="utf-8")

    calls = []

    def fake_runner(args, cwd, env=None):
        calls.append((args, cwd, env))
        new_file = dist_dir / "demo_pkg-0.1.0-py3-none-any.whl"
        new_file.write_text("wheel", encoding="utf-8")
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": "build ok",
                "stderr": "",
                "args": args,
            },
        )()

    result, files = build_package(project_dir, dist_dir, clean=True, runner=fake_runner)

    assert stale_file.exists() is False
    assert calls[0][0][:3] == [sys.executable, "-m", "build"]
    assert result.stdout == "build ok"
    assert files == [dist_dir.resolve() / "demo_pkg-0.1.0-py3-none-any.whl"]


def test_check_distributions_requires_existing_build_artifacts(tmp_path):
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)

    with pytest.raises(PyPICommandError):
        check_distributions(project_dir, project_dir / "dist")


def test_publish_distributions_builds_twine_command_and_env(tmp_path):
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    dist_dir.mkdir()
    artifact = dist_dir / "demo_pkg-0.1.0-py3-none-any.whl"
    artifact.write_text("wheel", encoding="utf-8")
    captured = {}

    def fake_runner(args, cwd, env=None):
        captured["args"] = args
        captured["cwd"] = cwd
        captured["env"] = env
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": "upload ok",
                "stderr": "",
                "args": args,
            },
        )()

    result, files = publish_distributions(
        project_dir,
        dist_dir,
        repository="testpypi",
        skip_existing=True,
        username="__token__",
        password="secret-token",
        runner=fake_runner,
    )

    assert captured["args"][:4] == [sys.executable, "-m", "twine", "upload"]
    assert "--repository" in captured["args"]
    assert "--skip-existing" in captured["args"]
    assert "--non-interactive" in captured["args"]
    assert captured["env"]["TWINE_USERNAME"] == "__token__"
    assert captured["env"]["TWINE_PASSWORD"] == "secret-token"
    assert result.stdout == "upload ok"
    assert files == [artifact.resolve()]


def test_release_package_runs_build_check_publish_in_order(tmp_path):
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    dist_dir.mkdir()
    artifact = dist_dir / "demo_pkg-0.1.0-py3-none-any.whl"
    calls = []

    def fake_runner(args, cwd, env=None):
        calls.append(args)
        if args[2] == "build":
            artifact.write_text("wheel", encoding="utf-8")
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": "ok",
                "stderr": "",
                "args": args,
            },
        )()

    summary = release_package(project_dir, dist_dir, runner=fake_runner)

    assert [call[2:] for call in calls] == [
        ["build", "--outdir", str(dist_dir)],
        ["twine", "check", str(artifact.resolve())],
        ["twine", "upload", "--repository", "testpypi", "--non-interactive", str(artifact.resolve())],
    ]
    assert summary["files"] == [artifact.resolve()]


def test_normalize_module_name_rewrites_hyphenated_package_name():
    assert normalize_module_name("my-chat") == "my_chat"


def test_scaffold_package_creates_expected_src_layout(tmp_path):
    project_dir = tmp_path / "mychat"

    result = scaffold_package(
        package_name="mychat",
        project_dir=project_dir,
        description="My chat package",
        author="Rex",
        email="rex@example.com",
    )

    assert result.module_name == "mychat"
    assert (project_dir / "pyproject.toml").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / "LICENSE").exists()
    assert (project_dir / ".gitignore").exists()
    assert (project_dir / "src" / "mychat" / "__init__.py").exists()
    assert (project_dir / "tests" / "conftest.py").exists()
    assert (project_dir / "tests" / "test_version.py").exists()
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "mychat"' in pyproject_text
    assert 'version = {attr = "mychat.__version__"}' in pyproject_text
    assert 'license = "MIT"' in pyproject_text
    assert 'authors = [{name = "Rex", email = "rex@example.com"}]' in pyproject_text


def test_scaffold_package_generated_project_pytest_passes(tmp_path):
    project_dir = tmp_path / "mychat"
    scaffold_package(
        package_name="mychat",
        project_dir=project_dir,
        description="My chat package",
    )

    result = sys.executable
    import subprocess

    process = subprocess.run(
        [result, "-m", "pytest", "-q"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    assert process.returncode == 0, process.stdout + process.stderr
    assert "1 passed" in process.stdout


def test_scaffold_package_rejects_non_empty_target_directory(tmp_path):
    project_dir = tmp_path / "mychat"
    project_dir.mkdir()
    (project_dir / "existing.txt").write_text("data", encoding="utf-8")

    with pytest.raises(PyPICommandError):
        scaffold_package("mychat", project_dir)
