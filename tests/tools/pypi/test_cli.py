from pathlib import Path

from click.testing import CliRunner
import pytest

from chattool.client.main import cli as root_cli
import chattool.tools.pypi.cli as pypi_cli


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


def test_root_cli_registers_pypi_group():
    runner = CliRunner()
    result = runner.invoke(root_cli, ["pypi", "--help"])

    assert result.exit_code == 0
    assert "init" in result.output
    assert "build" in result.output
    assert "check" in result.output
    assert "upload" in result.output
    assert "probe" in result.output
    assert "doctor" not in result.output
    assert "publish" not in result.output
    assert "release" not in result.output


def test_init_command_creates_package_scaffold(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "mychat"

    result = runner.invoke(
        pypi_cli.cli,
        [
            "init",
            "mychat",
            "--project-dir",
            str(project_dir),
            "--description",
            "My chat package",
        ],
    )

    assert result.exit_code == 0
    assert "Created Python package scaffold: mychat" in result.output
    assert (project_dir / "pyproject.toml").exists()
    assert (project_dir / "src" / "mychat" / "__init__.py").exists()
    assert (project_dir / "tests" / "conftest.py").exists()
    assert (project_dir / "tests" / "test_version.py").exists()


def test_init_command_requires_package_name_when_project_dir_missing():
    runner = CliRunner()

    result = runner.invoke(
        pypi_cli.cli,
        ["init"],
    )

    assert result.exit_code != 0
    assert "Package name is required" in result.output


def test_init_command_uses_project_dir_name_without_prompt(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "mychat"

    result = runner.invoke(
        pypi_cli.cli,
        [
            "init",
            "--project-dir",
            str(project_dir),
        ],
    )

    assert result.exit_code == 0
    assert (project_dir / "pyproject.toml").exists()


def test_build_and_check_commands_render_file_lists(monkeypatch, tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    dist_dir.mkdir()
    wheel = dist_dir / "demo_pkg-0.1.0-py3-none-any.whl"
    wheel.write_text("wheel", encoding="utf-8")

    monkeypatch.setattr(
        pypi_cli,
        "build_package",
        lambda *args, **kwargs: (
            type("Result", (), {"stdout": "build ok", "stderr": ""})(),
            [wheel.resolve()],
        ),
    )
    monkeypatch.setattr(
        pypi_cli,
        "check_distributions",
        lambda *args, **kwargs: (
            type("Result", (), {"stdout": "check ok", "stderr": ""})(),
            [wheel.resolve()],
        ),
    )

    build_result = runner.invoke(
        pypi_cli.cli,
        ["build", "--project-dir", str(project_dir)],
    )
    assert build_result.exit_code == 0
    assert f"Building distributions from {project_dir} into {dist_dir}..." in build_result.output
    assert "build ok" in build_result.output
    assert "Built distributions:" in build_result.output

    check_result = runner.invoke(
        pypi_cli.cli,
        ["check", "--project-dir", str(project_dir)],
    )
    assert check_result.exit_code == 0
    assert "check ok" in check_result.output
    assert "Checked distributions:" in check_result.output


def test_upload_command_uses_default_twine_behavior(monkeypatch, tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    dist_dir.mkdir()
    artifact = dist_dir / "demo_pkg-0.1.0-py3-none-any.whl"
    artifact.write_text("wheel", encoding="utf-8")
    captured = {}

    def fake_upload_distributions(project_dir, dist_dir, **kwargs):
        captured["project_dir"] = project_dir
        captured["dist_dir"] = dist_dir
        captured["kwargs"] = kwargs
        return type("Result", (), {"stdout": "upload ok", "stderr": ""})(), [artifact.resolve()]

    monkeypatch.setattr(pypi_cli, "upload_distributions", fake_upload_distributions)

    result = runner.invoke(
        pypi_cli.cli,
        ["upload", "--project-dir", str(project_dir), "--skip-existing"],
    )

    assert result.exit_code == 0
    assert f"Uploading distributions from {dist_dir} with `twine upload`..." in result.output
    assert "upload ok" in result.output
    assert "Uploaded distributions:" in result.output
    assert captured["kwargs"] == {"skip_existing": True}


def test_probe_command_reports_repository_conflicts(monkeypatch, tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)

    monkeypatch.setattr(
        pypi_cli,
        "check_repository_conflicts",
        lambda *args, **kwargs: [
            type("Check", (), {"status": "warn", "label": "repository.project", "detail": "demo-pkg already exists", "hint": None})(),
            type("Check", (), {"status": "ok", "label": "repository.version", "detail": "demo-pkg==0.1.0 is available", "hint": None})(),
        ],
    )

    result = runner.invoke(
        pypi_cli.cli,
        ["probe", "--project-dir", str(project_dir)],
    )

    assert result.exit_code == 0
    assert "[WARN] repository.project: demo-pkg already exists" in result.output
    assert "[OK] repository.version: demo-pkg==0.1.0 is available" in result.output
