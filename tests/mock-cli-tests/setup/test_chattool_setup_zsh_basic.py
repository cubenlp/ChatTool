import pytest

from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_zsh_writes_alias_files_idempotently(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        "chattool.setup.zsh.shutil.which",
        lambda name: "/usr/bin/zsh" if name == "zsh" else f"/usr/bin/{name}",
    )
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("# existing zshrc\n", encoding="utf-8")

    runner = CliRunner()
    first = runner.invoke(cli, ["setup", "zsh", "--no-omz", "-I"])
    second = runner.invoke(cli, ["setup", "zsh", "--no-omz", "-I"])

    assert first.exit_code == 0
    assert second.exit_code == 0

    zshrc_content = zshrc.read_text(encoding="utf-8")
    aliases_content = (tmp_path / ".zsh_aliases").read_text(encoding="utf-8")
    bash_profile_content = (tmp_path / ".bash_profile").read_text(encoding="utf-8")
    assert "# existing zshrc" in zshrc_content
    assert zshrc_content.count("# >>> chattool zsh alias source >>>") == 1
    assert aliases_content.count("# >>> chattool zsh aliases >>>") == 1
    assert 'alias copy="xclip -selection clipboard"' in aliases_content
    assert 'alias c7="CUDA_VISIBLE_DEVICES=7"' in aliases_content
    assert "alias pypi='pip install -i https://pypi.python.org/simple'" in aliases_content
    assert 'alias ollama="docker exec ollama ollama"' not in aliases_content
    assert bash_profile_content.count("# >>> chattool zsh login >>>") == 1


def test_setup_zsh_missing_zsh_exits_with_apt_hint(monkeypatch):
    monkeypatch.setattr(
        "chattool.setup.zsh.shutil.which",
        lambda name: "/usr/bin/git" if name == "git" else None,
    )

    result = CliRunner().invoke(
        cli,
        ["setup", "zsh", "--no-omz", "--no-aliases", "-I"],
    )

    assert result.exit_code != 0
    assert "zsh not found." in result.output
    assert "Please install it first: sudo apt install zsh -y" in result.output


def test_setup_zsh_missing_git_exits_with_apt_hint(monkeypatch):
    monkeypatch.setattr(
        "chattool.setup.zsh.shutil.which",
        lambda name: "/usr/bin/zsh" if name == "zsh" else None,
    )

    result = CliRunner().invoke(
        cli,
        ["setup", "zsh", "--no-aliases", "--no-login-shell", "-I"],
    )

    assert result.exit_code != 0
    assert "git not found." in result.output
    assert "Please install it first: sudo apt install git -y" in result.output


def test_setup_zsh_does_not_prompt_for_plugins_without_i(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        "chattool.setup.zsh.resolve_interactive_mode",
        lambda **kwargs: (None, True, False, False, False),
    )
    monkeypatch.setattr(
        "chattool.setup.zsh.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"zsh", "git"} else None,
    )

    def _unexpected_prompt(*args, **kwargs):
        raise AssertionError("plugin checkbox should only open when -i forces interactive")

    def _fake_ensure_omz(zshrc, selected_plugins):
        captured["plugins"] = selected_plugins

    monkeypatch.setattr("chattool.setup.zsh.ask_checkbox_with_controls", _unexpected_prompt)
    monkeypatch.setattr("chattool.setup.zsh._ensure_omz", _fake_ensure_omz)

    result = CliRunner().invoke(
        cli,
        ["setup", "zsh", "--no-aliases", "--no-login-shell"],
    )

    assert result.exit_code == 0
    assert captured["plugins"] == [
        "git",
        "sudo",
        "z",
        "zsh-syntax-highlighting",
        "zsh-autosuggestions",
        "zsh-completions",
    ]


def test_setup_zsh_i_prompts_for_plugin_candidates(monkeypatch, tmp_path):
    prompts = []
    captured = {}
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        "chattool.setup.zsh.resolve_interactive_mode",
        lambda **kwargs: (True, True, True, False, True),
    )
    monkeypatch.setattr(
        "chattool.setup.zsh.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"zsh", "git"} else None,
    )

    def _fake_checkbox(message, *args, **kwargs):
        prompts.append((message, kwargs.get("default_values")))
        if message == "Select zsh setup options":
            return ["omz"]
        if message == "Select oh-my-zsh plugins":
            return ["git", "zsh-autosuggestions"]
        raise AssertionError(f"unexpected prompt: {message}")

    def _fake_ensure_omz(zshrc, selected_plugins):
        captured["plugins"] = selected_plugins

    monkeypatch.setattr("chattool.setup.zsh.ask_checkbox_with_controls", _fake_checkbox)
    monkeypatch.setattr("chattool.setup.zsh._ensure_omz", _fake_ensure_omz)

    result = CliRunner().invoke(
        cli,
        ["setup", "zsh", "--no-aliases", "--no-login-shell", "-i"],
    )

    assert result.exit_code == 0
    assert prompts == [
        (
            "Select zsh setup options",
            ["omz"],
        ),
        (
            "Select oh-my-zsh plugins",
            [
                "git",
                "sudo",
                "z",
                "zsh-syntax-highlighting",
                "zsh-autosuggestions",
                "zsh-completions",
            ],
        ),
    ]
    assert captured["plugins"] == ["git", "zsh-autosuggestions"]
    assert "Selected oh-my-zsh plugins: git, zsh-autosuggestions" in result.output


def test_setup_zsh_i_prompts_for_setup_options_with_default_values(monkeypatch, tmp_path):
    prompts = []
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        "chattool.setup.zsh.resolve_interactive_mode",
        lambda **kwargs: (True, True, True, False, True),
    )
    monkeypatch.setattr(
        "chattool.setup.zsh.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"zsh", "git"} else None,
    )

    def _fake_checkbox(message, *args, **kwargs):
        prompts.append((message, kwargs.get("default_values")))
        if message == "Select zsh setup options":
            return ["aliases", "login_shell"]
        raise AssertionError(f"unexpected prompt: {message}")

    monkeypatch.setattr("chattool.setup.zsh.ask_checkbox_with_controls", _fake_checkbox)
    monkeypatch.setattr(
        "chattool.setup.zsh._replace_managed_block",
        lambda *args, **kwargs: None,
    )

    result = CliRunner().invoke(cli, ["setup", "zsh", "-i"])

    assert result.exit_code == 0
    assert prompts == [
        (
            "Select zsh setup options",
            ["omz", "aliases", "login_shell"],
        )
    ]
    assert "Select oh-my-zsh plugins" not in result.output
    assert "Selected zsh setup options: aliases, login shell" in result.output
