import importlib

import pytest

from click.testing import CliRunner

from chattool.client.main import cli

cc_cli = importlib.import_module("chattool.tools.cc.cli")


pytestmark = pytest.mark.mock_cli


def test_cc_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["cc", "--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "start" in result.output


def test_cc_init_non_interactive(tmp_path):
    runner = CliRunner()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    config_path = tmp_path / "config.toml"

    result = runner.invoke(
        cli,
        [
            "cc",
            "init",
            "-I",
            "--agent",
            "claudecode",
            "--platform",
            "feishu",
            "--quiet",
            "--project",
            "demo",
            "--work-dir",
            str(work_dir),
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert config_path.exists()
    content = config_path.read_text(encoding="utf-8")
    assert "[[projects]]" in content
    assert 'name = "demo"' in content
    assert "quiet = true" in content


def test_cc_init_defaults_from_existing_config(tmp_path, monkeypatch):
    runner = CliRunner()
    import chattool.interaction.policy as interactive_policy

    monkeypatch.setattr(interactive_policy, "is_interactive_available", lambda: True)
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[[projects]]",
                'name = "demo-project"',
                "quiet = true",
                "",
                "[projects.agent]",
                'type = "opencode"',
                "",
                "[projects.agent.options]",
                f'work_dir = "{tmp_path}"',
                'mode = "default"',
                "",
                "[[projects.platforms]]",
                'type = "telegram"',
                "",
                "[projects.platforms.options]",
                'token = "test-token"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "cc",
            "init",
            "-i",
            "--config",
            str(config_path),
        ],
        input="y\n\n\n\n\n\n\nn\n",
    )

    assert result.exit_code == 0
    assert "配置文件已存在:" in result.output
    assert config_path.name in result.output
    assert result.output.index("配置文件已存在") < result.output.index("选择消息平台")
    assert "选择 Agent 类型" in result.output
    assert "选择消息平台" in result.output
    assert "项目名称" in result.output
    assert "默认 quiet 模式（隐藏思考和工具进度消息）" in result.output
    assert "是否沿用现有平台配置?" not in result.output


def test_cc_init_existing_config_cancelled_before_other_prompts(tmp_path, monkeypatch):
    runner = CliRunner()
    import chattool.interaction.policy as interactive_policy

    monkeypatch.setattr(interactive_policy, "is_interactive_available", lambda: True)
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[[projects]]",
                'name = "demo-project"',
                "",
                "[projects.agent]",
                'type = "codex"',
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "cc",
            "init",
            "-i",
            "--config",
            str(config_path),
        ],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "配置文件已存在:" in result.output
    assert "已取消" in result.output
    assert "选择消息平台" not in result.output
    assert "选择 Agent 类型" not in result.output


def test_cc_init_preserves_existing_platform_config_without_reprompt(
    tmp_path, monkeypatch
):
    runner = CliRunner()
    import chattool.interaction.policy as interactive_policy

    monkeypatch.setattr(interactive_policy, "is_interactive_available", lambda: True)
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[[projects]]",
                'name = "demo-project"',
                "quiet = true",
                "",
                "[projects.agent]",
                'type = "opencode"',
                "",
                "[projects.agent.options]",
                f'work_dir = "{tmp_path}"',
                'mode = "default"',
                "",
                "[[projects.platforms]]",
                'type = "telegram"',
                "",
                "[projects.platforms.options]",
                'token = "test-token"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "cc",
            "init",
            "-i",
            "--config",
            str(config_path),
        ],
        input="y\n\n\n\n\n\n\nn\n",
    )

    assert result.exit_code == 0
    content = config_path.read_text(encoding="utf-8")
    assert "quiet = true" in content
    assert 'token = "test-token"' in content
    assert "检测到已有平台配置" in result.output
    assert "是否填写平台鉴权信息?" in result.output


def test_cc_init_feishu_uses_chatenv_candidates(tmp_path, monkeypatch):
    runner = CliRunner()
    import chattool.interaction.policy as interactive_policy

    monkeypatch.setattr(interactive_policy, "is_interactive_available", lambda: True)
    monkeypatch.setattr(
        cc_cli,
        "_get_feishu_candidate_options",
        lambda: {
            "app_id": "env-app-id",
            "app_secret": "env-app-secret",
        },
    )
    monkeypatch.setattr(
        cc_cli,
        "_prompt_secret_with_optional_default",
        lambda label, default="": default or "entered-secret",
    )

    config_path = tmp_path / "config.toml"

    result = runner.invoke(
        cli,
        [
            "cc",
            "init",
            "-i",
            "--agent",
            "claudecode",
            "--platform",
            "feishu",
            "--config",
            str(config_path),
        ],
        input="\n\n\n\nY\n\n",
    )

    assert result.exit_code == 0
    assert "检测到 chatenv 飞书配置候选" in result.output
    assert "app_id" in result.output
    assert "是否沿用默认 app_secret?" not in result.output
    content = config_path.read_text(encoding="utf-8")
    assert 'app_id = "env-app-id"' in content
    assert 'app_secret = "env-app-secret"' in content


def test_cc_start_retries_until_failure_threshold(tmp_path, monkeypatch):
    runner = CliRunner()
    config_path = tmp_path / "config.toml"
    config_path.write_text('[[projects]]\nname = "demo"\n', encoding="utf-8")

    attempts = []
    monkeypatch.setattr(cc_cli, "_check_binary", lambda name: "/usr/bin/cc-connect")
    monkeypatch.setattr(cc_cli.time, "sleep", lambda seconds: None)

    def fake_stream(cmd, env):
        attempts.append(list(cmd))
        return 2

    monkeypatch.setattr(cc_cli, "_stream_process", fake_stream)

    result = runner.invoke(
        cli,
        [
            "cc",
            "start",
            "--config",
            str(config_path),
            "--max-failures",
            "3",
            "--retry-delay",
            "0",
        ],
    )

    assert result.exit_code != 0
    assert len(attempts) == 3
    assert "cc-connect 启动失败 (1/3): exit code 2" in result.output
    assert "cc-connect 启动失败 (3/3): exit code 2" in result.output
    assert (
        "cc-connect 连续失败 3 次，已停止重试。最后错误: exit code 2" in result.output
    )


def test_cc_start_recovers_before_failure_threshold(tmp_path, monkeypatch):
    runner = CliRunner()
    config_path = tmp_path / "config.toml"
    config_path.write_text('[[projects]]\nname = "demo"\n', encoding="utf-8")

    attempts = []
    exits = iter([1, 1, 0])
    monkeypatch.setattr(cc_cli, "_check_binary", lambda name: "/usr/bin/cc-connect")
    monkeypatch.setattr(cc_cli.time, "sleep", lambda seconds: None)

    def fake_stream(cmd, env):
        attempts.append(list(cmd))
        return next(exits)

    monkeypatch.setattr(cc_cli, "_stream_process", fake_stream)

    result = runner.invoke(
        cli,
        [
            "cc",
            "start",
            "--config",
            str(config_path),
            "--max-failures",
            "5",
            "--retry-delay",
            "0",
        ],
    )

    assert result.exit_code == 0
    assert len(attempts) == 3
    assert "cc-connect 启动失败 (1/5): exit code 1" in result.output
    assert "cc-connect 已正常退出。" in result.output
