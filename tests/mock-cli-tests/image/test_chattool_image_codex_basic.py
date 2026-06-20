import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_image_codex_generate_prompts_and_writes_default_output(
    runner, monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: "a moon fox",
    )

    class FakeGenerator:
        host_model = "gpt-5.4"
        image_model = "gpt-image-2-medium"

        def generate(self, prompt):
            assert prompt == "a moon fox"
            return b"pngbytes"

    monkeypatch.setattr(
        "chattool.tools.image.cli.create_generator",
        lambda name, **kwargs: FakeGenerator(),
    )

    result = runner.invoke(cli, ["image", "codex", "generate"], catch_exceptions=False)

    assert result.exit_code == 0
    generated_files = list((tmp_path / "generated").glob("image_codex_*.png"))
    assert len(generated_files) == 1
    assert generated_files[0].read_bytes() == b"pngbytes"
    assert "Image saved to" in result.output


def test_chattool_image_codex_generate_forwards_overrides(
    runner, monkeypatch, tmp_path
):
    captured = {}
    output_path = tmp_path / "fox.png"

    class FakeGenerator:
        host_model = "gpt-5.4"
        image_model = "gpt-image-2-high"

        def generate(self, prompt):
            captured["prompt"] = prompt
            return b"foxpng"

    def fake_create_generator(name, **kwargs):
        captured["provider"] = name
        captured["kwargs"] = kwargs
        return FakeGenerator()

    monkeypatch.setattr(
        "chattool.tools.image.cli.create_generator", fake_create_generator
    )

    result = runner.invoke(
        cli,
        [
            "image",
            "codex",
            "generate",
            "a fox",
            "--aspect-ratio",
            "portrait",
            "--image-model",
            "gpt-image-2-high",
            "--host-model",
            "gpt-5.4",
            "--base-url",
            "https://example.test/codex",
            "--timeout",
            "12",
            "--output",
            str(output_path),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert captured["provider"] == "codex"
    assert captured["prompt"] == "a fox"
    assert captured["kwargs"] == {
        "base_url": "https://example.test/codex",
        "host_model": "gpt-5.4",
        "image_model": "gpt-image-2-high",
        "aspect_ratio": "portrait",
        "timeout_seconds": 12.0,
    }
    assert output_path.read_bytes() == b"foxpng"
    assert f"Image saved to {output_path}" in result.output


def test_chattool_image_codex_generate_failure_returns_nonzero(runner, monkeypatch):
    class FailingGenerator:
        host_model = "gpt-5.4"
        image_model = "gpt-image-2-medium"

        def generate(self, prompt):
            raise RuntimeError("token unavailable")

    monkeypatch.setattr(
        "chattool.tools.image.cli.create_generator",
        lambda name, **kwargs: FailingGenerator(),
    )

    result = runner.invoke(
        cli,
        ["image", "codex", "generate", "a fox", "-I"],
    )

    assert result.exit_code != 0
    assert "Error: token unavailable" in result.output
