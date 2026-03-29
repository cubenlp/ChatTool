from pathlib import Path

from click.testing import CliRunner

from chattool.client.main import cli as root_cli
from chattool.setup.uv import (
    _infer_python_version,
    _render_activation_block,
    _render_uv_index_block,
    _sync_command_args,
    setup_uv,
)


def _write_demo_pyproject(path: Path, with_dev: bool = True) -> None:
    optional_dev = """
[project.optional-dependencies]
dev = ["pytest"]
""" if with_dev else ""
    path.write_text(
        (
            "[project]\n"
            'name = "demo"\n'
            'version = "0.1.0"\n'
            "classifiers = [\n"
            '  "Programming Language :: Python :: 3.10",\n'
            '  "Programming Language :: Python :: 3.12",\n'
            "]\n"
            f"{optional_dev}\n"
        ),
        encoding="utf-8",
    )


def test_root_cli_registers_setup_uv():
    runner = CliRunner()

    result = runner.invoke(root_cli, ["setup", "--help"])

    assert result.exit_code == 0
    assert "uv" in result.output


def test_render_uv_blocks():
    block = _render_uv_index_block("https://example.com/simple/")
    assert 'url = "https://example.com/simple/"' in block
    assert "[[index]]" in block

    activate = _render_activation_block(Path("/tmp/demo"))
    assert "source /tmp/demo/.venv/bin/activate" in activate


def test_infer_python_version_prefers_highest_classifier(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    _write_demo_pyproject(pyproject)
    data = {
        "project": {
            "classifiers": [
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.12",
            ]
        }
    }

    version = _infer_python_version(tmp_path, data)

    assert version == "3.12"


def test_sync_command_args_for_dev_extra():
    assert _sync_command_args(include_dev=True, has_dev_extra=True) == ["sync", "--extra", "dev"]
    assert _sync_command_args(include_dev=False, has_dev_extra=True) == ["sync"]
    assert _sync_command_args(include_dev=True, has_dev_extra=False) == ["sync"]


def test_setup_uv_runs_pin_lock_and_sync(tmp_path, monkeypatch):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    _write_demo_pyproject(project_dir / "pyproject.toml")

    commands = []
    configured = {}

    monkeypatch.setattr("chattool.setup.uv._ensure_uv_available", lambda interactive, can_prompt: "/tmp/fake-uv")
    monkeypatch.setattr(
        "chattool.setup.uv._run_uv_or_abort",
        lambda uv_bin, cwd, args, label: commands.append((uv_bin, cwd, args, label)),
    )
    monkeypatch.setattr(
        "chattool.setup.uv._configure_uv_index",
        lambda default_index: configured.setdefault("index", default_index) or (tmp_path / "uv.toml"),
    )
    monkeypatch.setattr(
        "chattool.setup.uv._configure_shell_activation",
        lambda project_dir: configured.setdefault("activate", project_dir) or (tmp_path / ".zshrc"),
    )

    setup_uv(
        project_dir=project_dir,
        python_version="3.12",
        default_index="https://example.com/simple/",
        activate_shell=True,
        include_dev=True,
        interactive=False,
    )

    assert configured["index"] == "https://example.com/simple/"
    assert configured["activate"] == project_dir
    assert commands == [
        ("/tmp/fake-uv", project_dir, ["python", "pin", "3.12"], "python pin"),
        ("/tmp/fake-uv", project_dir, ["lock"], "lock"),
        ("/tmp/fake-uv", project_dir, ["sync", "--extra", "dev"], "sync"),
    ]


def test_setup_uv_defaults_to_dev_extra_when_present(tmp_path, monkeypatch):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    _write_demo_pyproject(project_dir / "pyproject.toml", with_dev=True)

    commands = []

    monkeypatch.setattr("chattool.setup.uv._ensure_uv_available", lambda interactive, can_prompt: "/tmp/fake-uv")
    monkeypatch.setattr(
        "chattool.setup.uv._run_uv_or_abort",
        lambda uv_bin, cwd, args, label: commands.append(args),
    )

    setup_uv(
        project_dir=project_dir,
        python_version="3.12",
        activate_shell=False,
        interactive=False,
    )

    assert commands[-1] == ["sync", "--extra", "dev"]
