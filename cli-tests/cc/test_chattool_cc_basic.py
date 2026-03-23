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
                "",
                "[projects.agent]",
                "type = \"opencode\"",
                "",
                "[projects.agent.options]",
                f"work_dir = \"{tmp_path}\"",
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
        input="\n\n\n\n\nn\n",
    )

    assert result.exit_code == 0
    assert "选择 Agent 类型" in result.output
    assert "[opencode]" in result.output
    assert "选择消息平台" in result.output
    assert "[telegram]" in result.output
    assert "项目名称 [demo-project]" in result.output


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
        input="\n\n\nY\n\nY\n",
    )

    assert result.exit_code == 0
    assert "检测到 chatenv 飞书配置候选" in result.output
    assert "app_id [env-app-id]" in result.output
    content = config_path.read_text(encoding="utf-8")
    assert 'app_id = "env-app-id"' in content
    assert 'app_secret = "env-app-secret"' in content
