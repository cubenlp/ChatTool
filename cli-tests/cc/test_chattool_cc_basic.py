import importlib

from click.testing import CliRunner

from chattool.client.main import cli

cc_cli = importlib.import_module("chattool.tools.cc.cli")


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
    assert "name = \"demo\"" in content
    assert "quiet = true" in content


def test_cc_init_defaults_from_existing_config(tmp_path, monkeypatch):
    runner = CliRunner()
    import chattool.setup.interactive as interactive_policy
    monkeypatch.setattr(interactive_policy, "is_interactive_available", lambda: True)
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[[projects]]",
                "name = \"demo-project\"",
                "quiet = true",
                "",
                "[projects.agent]",
                "type = \"opencode\"",
                "",
                "[projects.agent.options]",
                f"work_dir = \"{tmp_path}\"",
                "mode = \"default\"",
                "",
                "[[projects.platforms]]",
                "type = \"telegram\"",
                "",
                "[projects.platforms.options]",
                "token = \"test-token\"",
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
    assert f"配置文件已存在: {config_path}，是否覆盖? [y/N]:" in result.output
    assert result.output.index("是否覆盖?") < result.output.index("选择消息平台")
    assert "选择 Agent 类型" in result.output
    assert "[opencode]" in result.output
    assert "选择消息平台" in result.output
    assert "[telegram]" in result.output
    assert "项目名称 [demo-project]" in result.output
    assert "默认 quiet 模式（隐藏思考和工具进度消息）" in result.output
    assert "是否沿用现有平台配置?" not in result.output


def test_cc_init_existing_config_cancelled_before_other_prompts(tmp_path, monkeypatch):
    runner = CliRunner()
    import chattool.setup.interactive as interactive_policy

    monkeypatch.setattr(interactive_policy, "is_interactive_available", lambda: True)
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[[projects]]",
                "name = \"demo-project\"",
                "",
                "[projects.agent]",
                "type = \"codex\"",
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
    assert f"配置文件已存在: {config_path}，是否覆盖? [y/N]:" in result.output
    assert "已取消" in result.output
    assert "选择消息平台" not in result.output
    assert "选择 Agent 类型" not in result.output


def test_cc_init_preserves_existing_platform_config_without_reprompt(tmp_path, monkeypatch):
    runner = CliRunner()
    import chattool.setup.interactive as interactive_policy

    monkeypatch.setattr(interactive_policy, "is_interactive_available", lambda: True)
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[[projects]]",
                "name = \"demo-project\"",
                "quiet = true",
                "",
                "[projects.agent]",
                "type = \"opencode\"",
                "",
                "[projects.agent.options]",
                f"work_dir = \"{tmp_path}\"",
                "mode = \"default\"",
                "",
                "[[projects.platforms]]",
                "type = \"telegram\"",
                "",
                "[projects.platforms.options]",
                "token = \"test-token\"",
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
    import chattool.setup.interactive as interactive_policy

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
    assert "app_id [env-app-id]" in result.output
    assert "是否沿用默认 app_secret?" not in result.output
    content = config_path.read_text(encoding="utf-8")
    assert 'app_id = "env-app-id"' in content
    assert 'app_secret = "env-app-secret"' in content
