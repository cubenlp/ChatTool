from pathlib import Path

import pytest
from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = [pytest.mark.e2e]


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


def test_chattool_pypi_basic(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)

    doctor = runner.invoke(cli, ["pypi", "doctor", "--project-dir", str(project_dir)])
    assert "[OK] pyproject.toml" in doctor.output

    release = runner.invoke(
        cli,
        ["pypi", "release", "--project-dir", str(project_dir), "--dry-run"],
    )
    assert release.exit_code == 0
    assert "Release plan:" in release.output
    assert "Dry run only; no commands executed." in release.output
