from pathlib import Path
import sys

import pytest

from chattool.tools.pypi.main import (
    PyPICommandError,
    build_package,
    check_distributions,
    collect_doctor_checks,
    publish_distributions,
    release_package,
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
