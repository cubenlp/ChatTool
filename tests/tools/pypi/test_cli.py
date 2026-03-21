from pathlib import Path

from click.testing import CliRunner
import pytest

from chattool.client.main import cli as root_cli
import chattool.setup.interactive as interactive_policy
import chattool.tools.pypi.cli as pypi_cli
from chattool.utils.tui import BACK_VALUE


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


def _enable_interactive(monkeypatch) -> None:
    monkeypatch.setattr(pypi_cli, "is_interactive_available", lambda: True)
    monkeypatch.setattr(interactive_policy, "is_interactive_available", lambda: True)


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
    assert (project_dir / "tests" / "conftest.py").exists()
    assert (project_dir / "tests" / "test_version.py").exists()


def test_init_command_uses_tui_prompt_when_name_missing(tmp_path, monkeypatch):
    runner = CliRunner()
    prompts = []

    _enable_interactive(monkeypatch)
    monkeypatch.setattr(pypi_cli, "_git_config_default", lambda key: None)

    def fake_ask_text(message, default="", password=False, style=None):
        prompts.append((message, default, password))
        answers = {
            "Package name": "mychat",
            "project_dir": "mychat",
            "description": "mychat package",
            "requires_python": ">=3.10",
            "license": "MIT",
            "author (optional)": "",
            "email (optional)": "",
        }
        return answers[message]

    monkeypatch.setattr(pypi_cli, "ask_text", fake_ask_text)

    with runner.isolated_filesystem():
        result = runner.invoke(
            pypi_cli.cli,
            ["init"],
        )

        assert result.exit_code == 0
        assert prompts == [
            ("Package name", "", False),
            ("project_dir", "mychat", False),
            ("description", "mychat package", False),
            ("requires_python", ">=3.10", False),
            ("license", "MIT", False),
            ("author (optional)", "", False),
            ("email (optional)", "", False),
        ]
        assert "Starting interactive package scaffold..." in result.output
        assert Path("mychat", "pyproject.toml").exists()


def test_init_command_uses_project_dir_name_without_prompt(tmp_path, monkeypatch):
    runner = CliRunner()
    project_dir = tmp_path / "mychat"

    monkeypatch.setattr(
        pypi_cli,
        "ask_text",
        lambda *args, **kwargs: pytest.fail("ask_text should not be used when project_dir implies the package name"),
    )

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


def test_init_command_forced_interactive_prompts_defaults(monkeypatch, tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "mychat"
    prompts = []

    _enable_interactive(monkeypatch)
    monkeypatch.setattr(pypi_cli, "_git_config_default", lambda key: {"user.name": "Rex", "user.email": "rex@example.com"}.get(key))

    def fake_ask_text(message, default="", password=False, style=None):
        prompts.append((message, default, password))
        return default

    monkeypatch.setattr(pypi_cli, "ask_text", fake_ask_text)

    result = runner.invoke(
        pypi_cli.cli,
        ["init", "mychat", "--project-dir", str(project_dir), "-i"],
    )

    assert result.exit_code == 0
    assert prompts == [
        ("Package name", "mychat", False),
        ("project_dir", str(project_dir), False),
        ("description", "mychat package", False),
        ("requires_python", ">=3.10", False),
        ("license", "MIT", False),
        ("author (optional)", "Rex", False),
        ("email (optional)", "rex@example.com", False),
    ]


def test_init_command_aborts_when_tui_returns_back(monkeypatch):
    runner = CliRunner()

    _enable_interactive(monkeypatch)
    monkeypatch.setattr(pypi_cli, "ask_text", lambda *args, **kwargs: BACK_VALUE)

    result = runner.invoke(pypi_cli.cli, ["init"])

    assert result.exit_code != 0
    assert "Aborted!" in result.output


def test_doctor_command_reports_expected_checks(tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)

    result = runner.invoke(pypi_cli.cli, ["doctor", "--project-dir", str(project_dir)])

    assert "[OK] pyproject.toml" in result.output
    assert "project.version" in result.output
    assert result.exit_code in (0, 1)


def test_doctor_command_forced_interactive_prompts_defaults(monkeypatch, tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    prompts = []

    _enable_interactive(monkeypatch)

    def fake_ask_text(message, default="", password=False, style=None):
        prompts.append((message, default, password))
        return default

    monkeypatch.setattr(pypi_cli, "ask_text", fake_ask_text)

    result = runner.invoke(
        pypi_cli.cli,
        ["doctor", "--project-dir", str(project_dir), "-i"],
    )

    assert result.exit_code in (0, 1)
    assert prompts == [
        ("project_dir", str(project_dir), False),
        ("dist_dir", str(dist_dir), False),
    ]
    assert "Starting interactive package doctor..." in result.output


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


def test_build_command_forced_interactive_prompts_defaults(monkeypatch, tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    prompts = []
    confirms = []
    dist_dir = project_dir / "dist"

    _enable_interactive(monkeypatch)

    def fake_ask_text(message, default="", password=False, style=None):
        prompts.append((message, default, password))
        return default

    def fake_ask_confirm(message, default=True, style=None):
        confirms.append((message, default))
        return default

    monkeypatch.setattr(pypi_cli, "ask_text", fake_ask_text)
    monkeypatch.setattr(pypi_cli, "ask_confirm", fake_ask_confirm)
    monkeypatch.setattr(
        pypi_cli,
        "build_package",
        lambda *args, **kwargs: (
            type("Result", (), {"stdout": "build ok", "stderr": ""})(),
            [dist_dir / "demo_pkg-0.1.0-py3-none-any.whl"],
        ),
    )

    result = runner.invoke(
        pypi_cli.cli,
        ["build", "--project-dir", str(project_dir), "-i"],
    )

    assert result.exit_code == 0
    assert prompts == [
        ("project_dir", str(project_dir), False),
        ("dist_dir", str(dist_dir), False),
        ("build_target", "both", False),
    ]
    assert confirms == [("clean old dist artifacts?", True)]
    assert "Starting interactive package build..." in result.output


def test_check_command_forced_interactive_prompts_defaults(monkeypatch, tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    dist_dir.mkdir()
    artifact = dist_dir / "demo_pkg-0.1.0-py3-none-any.whl"
    artifact.write_text("wheel", encoding="utf-8")
    prompts = []
    confirms = []

    _enable_interactive(monkeypatch)

    def fake_ask_text(message, default="", password=False, style=None):
        prompts.append((message, default, password))
        return default

    def fake_ask_confirm(message, default=True, style=None):
        confirms.append((message, default))
        return default

    monkeypatch.setattr(pypi_cli, "ask_text", fake_ask_text)
    monkeypatch.setattr(pypi_cli, "ask_confirm", fake_ask_confirm)
    monkeypatch.setattr(
        pypi_cli,
        "check_distributions",
        lambda *args, **kwargs: (
            type("Result", (), {"stdout": "check ok", "stderr": ""})(),
            [artifact.resolve()],
        ),
    )

    result = runner.invoke(
        pypi_cli.cli,
        ["check", "--project-dir", str(project_dir), "-i"],
    )

    assert result.exit_code == 0
    assert prompts == [
        ("project_dir", str(project_dir), False),
        ("dist_dir", str(dist_dir), False),
    ]
    assert confirms == [("strict twine check?", False)]
    assert "Starting interactive package check..." in result.output


def test_publish_command_forced_interactive_prompts_defaults(monkeypatch, tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    dist_dir.mkdir()
    artifact = dist_dir / "demo_pkg-0.1.0-py3-none-any.whl"
    artifact.write_text("wheel", encoding="utf-8")
    prompts = []
    confirms = []
    captured = {}

    _enable_interactive(monkeypatch)

    def fake_ask_text(message, default="", password=False, style=None):
        prompts.append((message, default, password))
        if password:
            return "secret-token"
        return default

    def fake_ask_confirm(message, default=True, style=None):
        confirms.append((message, default))
        return True if message == "Publish to the real PyPI index?" else default

    def fake_publish_distributions(project_dir, dist_dir, **kwargs):
        captured["project_dir"] = project_dir
        captured["dist_dir"] = dist_dir
        captured["kwargs"] = kwargs
        return type("Result", (), {"stdout": "publish ok", "stderr": ""})(), [artifact.resolve()]

    monkeypatch.setattr(pypi_cli, "ask_text", fake_ask_text)
    monkeypatch.setattr(pypi_cli, "ask_confirm", fake_ask_confirm)
    monkeypatch.setattr(pypi_cli, "publish_distributions", fake_publish_distributions)

    result = runner.invoke(
        pypi_cli.cli,
        ["publish", "--project-dir", str(project_dir), "--repository", "pypi", "-i"],
    )

    assert result.exit_code == 0
    assert prompts == [
        ("project_dir", str(project_dir), False),
        ("dist_dir", str(dist_dir), False),
        ("repository", "pypi", False),
        ("repository_url (optional)", "", False),
        ("twine username (optional)", "__token__", False),
        ("twine password (optional)", "", True),
    ]
    assert confirms == [
        ("skip_existing", False),
        ("Publish to the real PyPI index?", False),
    ]
    assert captured["kwargs"]["repository"] == "pypi"
    assert captured["kwargs"]["username"] == "__token__"
    assert captured["kwargs"]["password"] == "secret-token"
    assert captured["kwargs"]["non_interactive"] is False
    assert "Starting interactive package publish..." in result.output


def test_release_dry_run_forced_interactive_prompts_defaults(monkeypatch, tmp_path):
    runner = CliRunner()
    project_dir = tmp_path / "pkg"
    project_dir.mkdir()
    _write_minimal_project(project_dir)
    dist_dir = project_dir / "dist"
    prompts = []
    confirms = []

    _enable_interactive(monkeypatch)

    def fake_ask_text(message, default="", password=False, style=None):
        prompts.append((message, default, password))
        return default

    def fake_ask_confirm(message, default=True, style=None):
        confirms.append((message, default))
        return default

    monkeypatch.setattr(pypi_cli, "ask_text", fake_ask_text)
    monkeypatch.setattr(pypi_cli, "ask_confirm", fake_ask_confirm)

    result = runner.invoke(
        pypi_cli.cli,
        ["release", "--project-dir", str(project_dir), "--dry-run", "-i"],
    )

    assert result.exit_code == 0
    assert prompts == [
        ("project_dir", str(project_dir), False),
        ("dist_dir", str(dist_dir), False),
        ("repository", "testpypi", False),
        ("repository_url (optional)", "", False),
        ("twine username (optional)", "__token__", False),
        ("twine password (optional)", "", True),
        ("build_target", "both", False),
    ]
    assert confirms == [
        ("skip_existing", False),
        ("clean old dist artifacts?", True),
        ("strict twine check?", False),
    ]
    assert "Starting interactive package release..." in result.output
    assert "Dry run only; no commands executed." in result.output


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
