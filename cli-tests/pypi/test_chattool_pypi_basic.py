from pathlib import Path

import pytest
from click.testing import CliRunner
import subprocess
import sys
import os

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
requires-python = ">=3.9"
license = {text = "MIT"}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")


def _pythonpath_with_fake_site(fake_site: Path) -> str:
    current = os.environ.get("PYTHONPATH")
    if current:
        return f"{fake_site}{os.pathsep}{current}"
    return str(fake_site)


def _write_fake_build_module(fake_site: Path) -> None:
    build_pkg = fake_site / "build"
    build_pkg.mkdir(parents=True, exist_ok=True)
    (build_pkg / "__init__.py").write_text("", encoding="utf-8")
    (build_pkg / "__main__.py").write_text(
        """
from pathlib import Path
import sys


def main() -> int:
    args = sys.argv[1:]
    outdir = Path(args[args.index("--outdir") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "demo_pkg-0.1.0-py3-none-any.whl").write_text("wheel", encoding="utf-8")
    (outdir / "demo_pkg-0.1.0.tar.gz").write_text("sdist", encoding="utf-8")
    print("fake build ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_fake_twine_module(fake_site: Path) -> None:
    twine_pkg = fake_site / "twine"
    twine_pkg.mkdir(parents=True, exist_ok=True)
    (twine_pkg / "__init__.py").write_text("", encoding="utf-8")
    (twine_pkg / "__main__.py").write_text(
        """
import sys


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        print("fake check ok")
        return 0
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_chattool_pypi_basic(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "mychat"
    dist_dir = project_dir / "dist"
    fake_site = tmp_path / "fake-site"

    init = runner.invoke(
        cli, ["pypi", "init", "mychat", "--project-dir", str(project_dir)]
    )
    assert init.exit_code == 0
    assert (project_dir / "src" / "mychat" / "__init__.py").exists()
    assert (project_dir / "tests" / "conftest.py").exists()
    assert 'requires-python = ">=3.9"' in (project_dir / "pyproject.toml").read_text(
        encoding="utf-8"
    )

    pytest_result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert pytest_result.returncode == 0, pytest_result.stdout + pytest_result.stderr
    assert "1 passed" in pytest_result.stdout

    _write_fake_build_module(fake_site)
    _write_fake_twine_module(fake_site)

    build = runner.invoke(
        cli,
        ["pypi", "build", "--project-dir", str(project_dir)],
        env={"PYTHONPATH": _pythonpath_with_fake_site(fake_site)},
    )
    assert build.exit_code == 0
    assert (
        f"Building distributions from {project_dir} into {dist_dir}..." in build.output
    )
    assert "Built distributions:" in build.output
    assert "fake build ok" in build.output

    check = runner.invoke(
        cli,
        ["pypi", "check", "--project-dir", str(project_dir)],
        env={"PYTHONPATH": _pythonpath_with_fake_site(fake_site)},
    )
    assert check.exit_code == 0
    assert "fake check ok" in check.output
    assert "Checked distributions:" in check.output


def test_chattool_pypi_init_cli_style_template(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "mychat-cli"

    result = runner.invoke(
        cli,
        [
            "pypi",
            "init",
            "mychat-cli",
            "--project-dir",
            str(project_dir),
            "--template",
            "cli-style",
        ],
    )

    assert result.exit_code == 0
    assert (project_dir / "DEVELOP.md").exists()
    assert (project_dir / "setup.md").exists()
    assert (project_dir / "CHANGELOG.md").exists()
    assert (project_dir / "AGENTS.md").exists()
    assert (project_dir / "docs" / "README.md").exists()
    assert (project_dir / "cli-tests" / "README.md").exists()
    assert (project_dir / "mock-cli-tests" / "README.md").exists()
    develop_text = (project_dir / "DEVELOP.md").read_text(encoding="utf-8")
    assert "CLI Rules" in develop_text
    assert "doc-first CLI testing" in develop_text
