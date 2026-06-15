from click.testing import CliRunner
from chatstyle import InteractiveResolution

from chattool.config import BaseEnvConfig, EnvField, OpenAIConfig
from chatenv.cli import cli


class MockConfig(BaseEnvConfig):
    _title = "Mock Configuration"
    _aliases = ["mock"]
    _storage_dir = "Mock"

    MOCK_KEY = EnvField("MOCK_KEY", default="default_mock")

    @classmethod
    def test(cls):
        click_output = getattr(cls, "_test_output", None)
        if click_output is not None:
            click_output.append("tested")


def test_cat_prefers_typed_env_over_shell_env(tmp_path, monkeypatch):
    home = tmp_path
    env_dir = home / "envs"
    env_file = env_dir / ".env"
    active_dir = env_dir / "Mock"
    active_dir.mkdir(parents=True)
    active_file = active_dir / ".env"
    active_file.write_text("MOCK_KEY='from_file'\n", encoding="utf-8")
    env_dir.mkdir(parents=True, exist_ok=True)
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("CHATARCH_HOME", str(home))

    monkeypatch.setattr("chattool.config.BaseEnvConfig._registry", [MockConfig])
    monkeypatch.setenv("MOCK_KEY", "from_env")

    result = CliRunner().invoke(cli, ["cat", "-t", "mock"])

    assert result.exit_code == 0
    assert "MOCK_KEY='from_file'" in result.output
    assert "from_env" not in result.output


def test_cat_profile_loads_profile_env_file(tmp_path, monkeypatch):
    home = tmp_path
    env_dir = home / "envs"
    env_file = env_dir / ".env"
    profile_dir = env_dir / "Mock"
    profile_dir.mkdir(parents=True)
    profile_file = profile_dir / "apple.env"
    profile_file.write_text("MOCK_KEY='from_profile'\n", encoding="utf-8")
    env_dir.mkdir(parents=True, exist_ok=True)
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("CHATARCH_HOME", str(home))

    monkeypatch.setattr("chattool.config.BaseEnvConfig._registry", [MockConfig])

    result = CliRunner().invoke(cli, ["cat", "-t", "mock", "apple"])

    assert result.exit_code == 0
    assert "MOCK_KEY='from_profile'" in result.output


def test_profile_and_key_commands_prompt_when_args_missing(tmp_path, monkeypatch):
    home = tmp_path
    env_dir = home / "envs"
    env_file = env_dir / ".env"
    env_dir.mkdir(parents=True, exist_ok=True)
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("CHATARCH_HOME", str(home))
    monkeypatch.setattr("chattool.config.BaseEnvConfig._registry", [MockConfig])
    monkeypatch.setattr(
        "chatstyle.input.resolve.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: InteractiveResolution(
            interactive=None,
            can_prompt=True,
            force_interactive=False,
            need_prompt=auto_prompt_condition,
        ),
    )

    answers = {
        "profile name": "demo",
        "key": "MOCK_KEY",
        "KEY=VALUE": "MOCK_KEY=updated",
    }
    monkeypatch.setattr(
        "chatstyle.tui.prompt.ask_text",
        lambda message, default="", password=False, style=None: answers[message],
    )
    monkeypatch.setattr(
        "chatenv.cli.ask_confirm", lambda message, default=False: True
    )

    active_dir = env_dir / "Mock"
    active_dir.mkdir(parents=True)
    active_file = active_dir / ".env"
    active_file.write_text("MOCK_KEY='from_file'\n", encoding="utf-8")
    profile_file = active_dir / "demo.env"
    profile_file.write_text("MOCK_KEY='from_profile'\n", encoding="utf-8")

    runner = CliRunner()
    save_result = runner.invoke(cli, ["save", "-t", "mock"], catch_exceptions=False)
    get_result = runner.invoke(cli, ["get"], catch_exceptions=False)
    set_result = runner.invoke(cli, ["set"], catch_exceptions=False)
    use_result = runner.invoke(cli, ["use", "-t", "mock"], catch_exceptions=False)
    delete_result = runner.invoke(cli, ["delete", "-t", "mock"], catch_exceptions=False)

    assert save_result.exit_code == 0
    assert get_result.exit_code == 0
    assert set_result.exit_code == 0
    assert use_result.exit_code == 0
    assert delete_result.exit_code == 0


def test_chatenv_get_errors_with_no_interaction():
    result = CliRunner().invoke(cli, ["get", "-I"])

    assert result.exit_code != 0
    assert "Missing required value: key" in result.output


def test_chatenv_test_prompts_for_target(tmp_path, monkeypatch):
    home = tmp_path
    env_dir = home / "envs"
    env_file = env_dir / ".env"
    env_dir.mkdir(parents=True, exist_ok=True)
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("CHATARCH_HOME", str(home))
    monkeypatch.setattr("chattool.config.BaseEnvConfig._registry", [MockConfig])
    monkeypatch.setattr(
        "chattool.config.elements.BaseEnvConfig._registry", [MockConfig]
    )
    monkeypatch.setattr(
        "chatstyle.input.resolve.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: InteractiveResolution(
            interactive=None,
            can_prompt=True,
            force_interactive=False,
            need_prompt=auto_prompt_condition,
        ),
    )
    monkeypatch.setattr(
        "chatstyle.tui.prompt.ask_text",
        lambda message, default="", password=False, style=None: "mock",
    )
    outputs = []
    MockConfig._test_output = outputs

    result = CliRunner().invoke(cli, ["test"], catch_exceptions=False)

    assert result.exit_code == 0
    assert outputs == ["tested"]


def test_chatenv_openai_test_uses_responses_api(monkeypatch, tmp_path):
    home = tmp_path
    env_dir = home / "envs"
    env_file = env_dir / ".env"
    env_dir.mkdir(parents=True, exist_ok=True)
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("CHATARCH_HOME", str(home))
    monkeypatch.setattr("chattool.config.BaseEnvConfig._registry", [OpenAIConfig])
    monkeypatch.setattr(OpenAIConfig.OPENAI_API_BASE, "value", "https://api.example/v1")
    monkeypatch.setattr(OpenAIConfig.OPENAI_API_KEY, "value", "sk-test")
    monkeypatch.setattr(OpenAIConfig.OPENAI_API_MODEL, "value", "gpt-5.5")

    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            return None

        def iter_lines(self):
            return iter([
                'event: response.created',
                'data: {"type":"response.created"}',
                'event: response.output_text.delta',
                'data: {"type":"response.output_text.delta","delta":"ok"}',
            ])

    class FakeClient:
        def __init__(self, timeout=None):
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def stream(self, method, url, json=None, headers=None):
            calls.append(
                {"method": method, "url": url, "json": json, "headers": headers}
            )
            return FakeResponse()

    monkeypatch.setattr("httpx.Client", FakeClient)

    result = CliRunner().invoke(cli, ["test", "-t", "oai"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Responses API generated" in result.output
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://api.example/v1/responses"
    assert calls[0]["json"]["input"] == [{"role": "user", "content": "hi"}]
    assert calls[0]["json"]["max_output_tokens"] == 8
    assert calls[0]["json"]["stream"] is True
