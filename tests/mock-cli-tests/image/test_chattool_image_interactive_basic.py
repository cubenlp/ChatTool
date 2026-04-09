from pathlib import Path

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_image_huggingface_generate_prompts_for_required_inputs(
    runner, monkeypatch, tmp_path
):
    answers = {
        "prompt": "a small robot",
        "output": str(tmp_path / "robot.png"),
    }
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: answers[message],
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_path",
        lambda message, default="", style=None: answers[message],
    )
    monkeypatch.setattr(
        "chattool.tools.image.cli.create_generator",
        lambda name: type(
            "FakeGen", (), {"generate": lambda self, prompt: b"pngbytes"}
        )(),
    )

    result = runner.invoke(
        cli, ["image", "huggingface", "generate"], catch_exceptions=False
    )

    assert result.exit_code == 0
    assert (tmp_path / "robot.png").exists()


def test_chattool_image_huggingface_generate_errors_with_no_interaction(runner):
    result = runner.invoke(cli, ["image", "huggingface", "generate", "-I"])

    assert result.exit_code != 0
    assert "Missing required value: prompt" in result.output
