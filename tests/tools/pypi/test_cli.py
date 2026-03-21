from pathlib import Path

from click.testing import CliRunner

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
    assert "doctor" in result.output
    assert "release" in result.output


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
    assert (project_dir / "tests" / "test_version.py").exists()


def test_doctor_command_reports_expected_checks(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)

    result = runner.invoke(pypi_cli.cli, ["doctor", "--project-dir", str(project_dir)])

    assert "[OK] pyproject.toml" in result.output
    assert "project.version" in result.output
    assert result.exit_code in (0, 1)


def test_release_dry_run_prints_plan(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)

    result = runner.invoke(
        pypi_cli.cli,
        ["release", "--project-dir", str(project_dir), "--dry-run"],
    )

    assert result.exit_code == 0
    assert "Release plan:" in result.output
    assert "step=build" in result.output
    assert "Dry run only; no commands executed." in result.output


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
    assert "build ok" in build_result.output
    assert "Built distributions:" in build_result.output

    check_result = runner.invoke(
        pypi_cli.cli,
        ["check", "--project-dir", str(project_dir)],
    )
    assert check_result.exit_code == 0
    assert "check ok" in check_result.output
    assert "Checked distributions:" in check_result.output


def test_publish_requires_yes_when_targeting_real_pypi(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    dist_dir.mkdir()
    (dist_dir / "demo_pkg-0.1.0-py3-none-any.whl").write_text("wheel", encoding="utf-8")

    result = runner.invoke(
        pypi_cli.cli,
        [
            "publish",
            "--project-dir",
            str(project_dir),
            "--repository",
            "pypi",
            "-I",
        ],
    )

    assert result.exit_code != 0
    assert "requires `--yes` or an interactive confirmation" in result.output
