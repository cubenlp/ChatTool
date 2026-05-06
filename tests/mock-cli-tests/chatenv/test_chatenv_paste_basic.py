from chattool.config import BaseEnvConfig, EnvField
from chattool.config.cli import cli


class MockOpenAIConfig(BaseEnvConfig):
    _title = "Mock OpenAI Configuration"
    _aliases = ["mock-openai"]
    _storage_dir = "MockOpenAI"

    MOCK_OPENAI_BASE = EnvField("MOCK_OPENAI_BASE", default="https://default/v1")
    MOCK_OPENAI_KEY = EnvField("MOCK_OPENAI_KEY", is_sensitive=True)
    MOCK_OPENAI_MODEL = EnvField("MOCK_OPENAI_MODEL", default="default-model")


class MockFeishuConfig(BaseEnvConfig):
    _title = "Mock Feishu Configuration"
    _aliases = ["mock-feishu"]
    _storage_dir = "MockFeishu"

    MOCK_FEISHU_APP_ID = EnvField("MOCK_FEISHU_APP_ID")
    MOCK_FEISHU_SECRET = EnvField("MOCK_FEISHU_SECRET", is_sensitive=True)


def _patch_env(monkeypatch, tmp_path, registry=None):
    env_dir = tmp_path / "envs"
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setattr("chattool.config.cli.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.config.cli.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr(
        "chattool.config.BaseEnvConfig._registry",
        registry or [MockOpenAIConfig, MockFeishuConfig],
    )
    return env_dir, env_file


def test_paste_imports_cat_output_into_active_typed_env(tmp_path, monkeypatch, runner):
    env_dir, _ = _patch_env(monkeypatch, tmp_path)
    active_dir = env_dir / "MockOpenAI"
    active_dir.mkdir(parents=True)
    (active_dir / ".env").write_text(
        "MOCK_OPENAI_MODEL='existing-model'\n", encoding="utf-8"
    )
    paste_text = "\n".join(
        [
            "MOCK_OPENAI_BASE='https://api.example.com/v1'",
            "MOCK_OPENAI_KEY='sk-one'",
            "MOCK_FEISHU_SECRET='secret-one'",
            "UNKNOWN_KEY='ignored'",
        ]
    )

    result = runner.invoke(
        cli, ["paste", "--stdin", "--yes"], input=paste_text
    )

    assert result.exit_code == 0
    assert "Parsed 3 recognized values in 2 config types" in result.output
    assert "MockOpenAI" in result.output
    assert "MockFeishu" in result.output
    assert "UNKNOWN_KEY" in result.output
    assert "sk-one" not in result.output
    assert "secret-one" not in result.output

    openai_env = (env_dir / "MockOpenAI" / ".env").read_text(encoding="utf-8")
    feishu_env = (env_dir / "MockFeishu" / ".env").read_text(encoding="utf-8")
    assert "MOCK_OPENAI_BASE='https://api.example.com/v1'" in openai_env
    assert "MOCK_OPENAI_KEY='sk-one'" in openai_env
    assert "MOCK_OPENAI_MODEL='existing-model'" in openai_env
    assert "MOCK_FEISHU_SECRET='secret-one'" in feishu_env


def test_paste_profile_writes_same_name_for_all_matched_types(
    tmp_path, monkeypatch, runner
):
    env_dir, _ = _patch_env(monkeypatch, tmp_path)
    openai_active = env_dir / "MockOpenAI" / ".env"
    feishu_active = env_dir / "MockFeishu" / ".env"
    openai_active.parent.mkdir(parents=True)
    feishu_active.parent.mkdir(parents=True)
    openai_active.write_text("MOCK_OPENAI_MODEL='active-model'\n", encoding="utf-8")
    feishu_active.write_text("MOCK_FEISHU_APP_ID='active-app'\n", encoding="utf-8")
    paste_text = "\n".join(
        [
            "MOCK_OPENAI_KEY='sk-profile'",
            "MOCK_FEISHU_SECRET='secret-profile'",
        ]
    )

    result = runner.invoke(
        cli, ["paste", "--value", paste_text, "--profile", "work", "--yes"]
    )

    assert result.exit_code == 0
    assert "Written values:" in result.output
    assert "MockOpenAI" in result.output
    assert "MockFeishu" in result.output
    assert "work.env" in result.output
    assert "MOCK_OPENAI_KEY" in result.output
    assert "MOCK_FEISHU_SECRET" in result.output
    assert openai_active.read_text(encoding="utf-8") == "MOCK_OPENAI_MODEL='active-model'\n"
    assert feishu_active.read_text(encoding="utf-8") == "MOCK_FEISHU_APP_ID='active-app'\n"

    openai_profile = (env_dir / "MockOpenAI" / "work.env").read_text(
        encoding="utf-8"
    )
    feishu_profile = (env_dir / "MockFeishu" / "work.env").read_text(
        encoding="utf-8"
    )
    assert "MOCK_OPENAI_KEY='sk-profile'" in openai_profile
    assert "MOCK_OPENAI_MODEL='active-model'" in openai_profile
    assert "MOCK_FEISHU_SECRET='secret-profile'" in feishu_profile
    assert "MOCK_FEISHU_APP_ID='active-app'" in feishu_profile


def test_paste_existing_profile_requires_yes_to_overwrite(
    tmp_path, monkeypatch, runner
):
    env_dir, _ = _patch_env(monkeypatch, tmp_path, registry=[MockOpenAIConfig])
    profile_path = env_dir / "MockOpenAI" / "work.env"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text("MOCK_OPENAI_KEY='old'\n", encoding="utf-8")
    monkeypatch.setattr("chattool.config.cli.is_interactive_available", lambda: False)

    result = runner.invoke(
        cli,
        [
            "paste",
            "--value",
            "MOCK_OPENAI_KEY='new'",
            "--profile",
            "work",
        ],
    )

    assert result.exit_code != 0
    assert "Existing profiles will be overwritten" in result.output
    assert "requires --yes" in result.output
    assert profile_path.read_text(encoding="utf-8") == "MOCK_OPENAI_KEY='old'\n"

    overwrite_result = runner.invoke(
        cli,
        [
            "paste",
            "--value",
            "MOCK_OPENAI_KEY='new'",
            "--profile",
            "work",
            "--yes",
        ],
    )

    assert overwrite_result.exit_code == 0
    assert "MOCK_OPENAI_KEY='new'" in profile_path.read_text(encoding="utf-8")


def test_paste_unknown_only_fails_without_writing(tmp_path, monkeypatch, runner):
    env_dir, _ = _patch_env(monkeypatch, tmp_path, registry=[MockOpenAIConfig])

    result = runner.invoke(cli, ["paste", "--value", "UNKNOWN_KEY='x'", "--yes"])

    assert result.exit_code != 0
    assert "No registered configuration keys found" in result.output
    assert not (env_dir / "MockOpenAI" / ".env").exists()


def test_paste_value_and_stdin_are_mutually_exclusive(tmp_path, monkeypatch, runner):
    _patch_env(monkeypatch, tmp_path, registry=[MockOpenAIConfig])

    result = runner.invoke(
        cli,
        [
            "paste",
            "--value",
            "MOCK_OPENAI_KEY='x'",
            "--stdin",
            "--yes",
        ],
        input="MOCK_OPENAI_KEY='from-stdin'\n",
    )

    assert result.exit_code != 0
    assert "--value and --stdin cannot be used together" in result.output



def test_paste_tolerates_terminal_transcript_prompts(tmp_path, monkeypatch, runner):
    env_dir, _ = _patch_env(monkeypatch, tmp_path, registry=[MockOpenAIConfig])
    transcript = """
> chatenv paste
Paste env text. Finish with an empty line:
>: MOCK_OPENAI_BASE='https://api.example.com/v1'
MOCK_OPENAI_KEY='sk-transcript'
╭─────────────────────────── Confirm ───────────────────────────╮
│ Write parsed values to active env files for 1 config type(s)? │
╰───────────────────────────────────────────────────────────────╯
Continue [y/N] y
>: >: MOCK_OPENAI_MODEL='model-from-prompt'
"""

    result = runner.invoke(cli, ["paste", "--value", transcript, "--yes"])

    assert result.exit_code == 0
    assert "could not parse" not in result.output
    active_env = (env_dir / "MockOpenAI" / ".env").read_text(encoding="utf-8")
    assert "MOCK_OPENAI_BASE='https://api.example.com/v1'" in active_env
    assert "MOCK_OPENAI_KEY='sk-transcript'" in active_env
    assert "MOCK_OPENAI_MODEL='model-from-prompt'" in active_env



def test_paste_interactive_can_choose_profile_name(tmp_path, monkeypatch, runner):
    env_dir, _ = _patch_env(monkeypatch, tmp_path, registry=[MockOpenAIConfig])
    monkeypatch.setattr("chattool.interaction.policy.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.config.cli.ask_text",
        lambda message, default="": "work",
    )
    monkeypatch.setattr(
        "chattool.config.cli.ask_confirm", lambda message, default=False: True
    )

    result = runner.invoke(
        cli, ["paste", "--value", "MOCK_OPENAI_KEY='sk-interactive'"]
    )

    assert result.exit_code == 0
    profile_file = env_dir / "MockOpenAI" / "work.env"
    assert profile_file.exists()
    assert "MOCK_OPENAI_KEY='sk-interactive'" in profile_file.read_text(
        encoding="utf-8"
    )
    assert not (env_dir / "MockOpenAI" / ".env").exists()



def test_paste_no_interactive_errors_without_value_or_stdin(
    tmp_path, monkeypatch, runner
):
    _patch_env(monkeypatch, tmp_path, registry=[MockOpenAIConfig])

    result = runner.invoke(cli, ["paste", "-I"])

    assert result.exit_code != 0
    assert "requires --value or --stdin" in result.output
