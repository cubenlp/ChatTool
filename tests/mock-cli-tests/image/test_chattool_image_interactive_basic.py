from pathlib import Path

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_image_huggingface_generate_prompts_for_required_inputs(
    runner, monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: "a small robot",
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
    generated_files = list((tmp_path / "generated").glob("image_huggingface_*.png"))
    assert len(generated_files) == 1
    assert generated_files[0].read_bytes() == b"pngbytes"


def test_chattool_image_huggingface_generate_errors_with_no_interaction(runner):
    result = runner.invoke(cli, ["image", "huggingface", "generate", "-I"])

    assert result.exit_code != 0
    assert "Missing required value: prompt" in result.output
