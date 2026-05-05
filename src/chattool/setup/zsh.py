from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import click

from chattool.interaction import (
    BACK_VALUE,
    abort_if_force_without_tty,
    ask_checkbox_with_controls,
    create_choice,
    resolve_interactive_mode,
)
from chattool.setup.alias import ALIAS_MAP
from chattool.utils.custom_logger import setup_logger

logger = setup_logger("setup_zsh")

ZSH_ALIASES_BEGIN = "# >>> chattool zsh aliases >>>"
ZSH_ALIASES_END = "# <<< chattool zsh aliases <<<"
ZSH_ALIASES_SOURCE_BEGIN = "# >>> chattool zsh alias source >>>"
ZSH_ALIASES_SOURCE_END = "# <<< chattool zsh alias source <<<"
ZSH_LOGIN_BEGIN = "# >>> chattool zsh login >>>"
ZSH_LOGIN_END = "# <<< chattool zsh login <<<"

OMZ_PLUGIN_CANDIDATES = (
    ("git", "git - oh-my-zsh built-in git aliases and completions"),
    ("sudo", "sudo - press Esc twice to prefix sudo"),
    ("z", "z - jump to frequently used directories"),
    ("zsh-syntax-highlighting", "zsh-syntax-highlighting - command syntax colors"),
    ("zsh-autosuggestions", "zsh-autosuggestions - command suggestions from history"),
    ("zsh-completions", "zsh-completions - extra completion definitions"),
)
DEFAULT_OMZ_PLUGINS = tuple(name for name, _ in OMZ_PLUGIN_CANDIDATES)
ZSH_SETUP_OPTION_CANDIDATES = (
    (
        "omz",
        "oh-my-zsh + plugins + powerlevel10k",
    ),
    (
        "aliases",
        "~/.zsh_aliases with QuickSetup and ChatTool aliases",
    ),
    (
        "login_shell",
        "~/.bash_profile handoff to zsh -l",
    ),
)
PLUGIN_REPOS = {
    "zsh-syntax-highlighting": "https://github.com/zsh-users/zsh-syntax-highlighting.git",
    "zsh-autosuggestions": "https://github.com/zsh-users/zsh-autosuggestions.git",
    "zsh-completions": "https://github.com/zsh-users/zsh-completions.git",
}
P10K_REPO = "https://github.com/romkatv/powerlevel10k.git"
OMZ_REPO = "https://github.com/ohmyzsh/ohmyzsh.git"
P10K_THEME = "powerlevel10k/powerlevel10k"

QUICKSETUP_ALIAS_BLOCK = r"""# disable update reminder
zstyle ':omz:update' mode disabled

# tmux
alias tl="tmux ls"
alias tn="tmux new -s"
alias ta="tmux attach -t"
alias tk="tmux kill-session -t"

# clipboard
alias copy="xclip -selection clipboard"

# tar
alias tarx="tar --use-compress-program=unpigz -xf"
alias tarc="tar --use-compress-program=unpigz -cf"

# edit zsh config
alias vzsh="vim ~/.zshrc"
alias valias="vim ~/.zsh_aliases"
alias szsh="source ~/.zshrc"
alias salias="source ~/.zsh_aliases"
alias czsh="code ~/.zshrc"
alias calias="code ~/.zsh_aliases"

# docker
alias dup="docker-compose up -d"
alias dpull="docker-compose pull"
alias dps="docker-compose ps"
alias ddown="docker-compose down"
alias drestart="docker-compose restart"
alias dlog="docker-compose logs -f"
dockerin(){
   docker exec -it $1 /bin/bash
}

# nginx
alias cdnginx="cd /etc/nginx/sites-available"
alias ngt="sudo nginx -t"
alias ngr="sudo nginx -s reload"

# conda
alias cda="conda activate"
alias cdd="conda deactivate"
alias cdls="conda env list"
alias cdrm="conda env remove --name"
# cuda
alias c0="CUDA_VISIBLE_DEVICES=0"
alias c1="CUDA_VISIBLE_DEVICES=1"
alias c2="CUDA_VISIBLE_DEVICES=2"
alias c3="CUDA_VISIBLE_DEVICES=3"
alias c4="CUDA_VISIBLE_DEVICES=4"
alias c5="CUDA_VISIBLE_DEVICES=5"
alias c6="CUDA_VISIBLE_DEVICES=6"
alias c7="CUDA_VISIBLE_DEVICES=7"

# Jupyter
addkernel (){
    python -m ipykernel install --name $1 --user
}

# pip install
alias tspip="pip install -i https://pypi.tuna.tsinghua.edu.cn/simple"
alias pypi='pip install -i https://pypi.python.org/simple'

# kill process
kport (){
    kill -9 `lsof -i:$1 -t`
}
skport () {sudo kill -9 `sudo lsof -i:$1 -t`}

# create short cut
lnfile() {
   ln $1 $HOME/.local/bin/
}
# sort by file size
dusort() {
   du -sh * | sort -h
}
sdusort(){
   sudo du -sh * | sort -h
}

# proxy
alias proxy_off="unset all_proxy"
alias ipinfo="curl http://ip-api.com/json/\?lang\=zh-CN"
# test network
curltest(){
    curl -I https://www.facebook.com
}
pingtest(){
    ping -c2 -i3 www.wzhecnu.cn
}
"""

def _configure_logger(log_level="INFO"):
    global logger
    logger = setup_logger("setup_zsh", log_level=str(log_level).upper())
    return logger


def _run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


def _ensure_success(result: subprocess.CompletedProcess, step_name: str) -> None:
    if result.returncode == 0:
        return
    detail = (result.stderr or result.stdout or "").strip()
    logger.error("%s failed: %s", step_name, detail)
    click.echo(f"{step_name} failed.", err=True)
    if detail:
        click.echo(detail, err=True)
    raise click.Abort()


def _replace_managed_block(path: Path, begin: str, end: str, block: str) -> None:
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    begin_idx = content.find(begin)
    end_idx = content.find(end)
    if begin_idx != -1 and end_idx != -1 and end_idx >= begin_idx:
        end_idx += len(end)
        if end_idx < len(content) and content[end_idx : end_idx + 1] == "\n":
            end_idx += 1
        content = content[:begin_idx] + content[end_idx:]
    content = content.rstrip("\n")
    block = block.rstrip("\n")
    if block:
        content = f"{content}\n\n{block}" if content else block
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + ("\n" if content else ""), encoding="utf-8")


def _upsert_line(path: Path, pattern: str, line: str) -> None:
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = content.splitlines()
    replaced = False
    compiled = re.compile(pattern)
    for idx, existing in enumerate(lines):
        if compiled.match(existing):
            lines[idx] = line
            replaced = True
            break
    if not replaced:
        lines.append(line)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


def select_omz_plugins_interactively(default_selected: list[str]) -> list[str]:
    choices = [
        create_choice(
            title=description,
            value=name,
            checked=name in default_selected,
        )
        for name, description in OMZ_PLUGIN_CANDIDATES
    ]
    selected = ask_checkbox_with_controls(
        "Select oh-my-zsh plugins",
        choices=choices,
        default_values=default_selected,
        instruction="(Use arrow keys to move, <space> to toggle, <a> to toggle all, <enter> to confirm)",
        select_all_label="Select all plugins",
    )
    if selected == BACK_VALUE:
        raise click.Abort()
    return list(selected or [])


def select_zsh_setup_options_interactively(
    install_omz: bool,
    aliases: bool,
    login_shell: bool,
) -> tuple[bool, bool, bool]:
    default_selected = []
    if install_omz:
        default_selected.append("omz")
    if aliases:
        default_selected.append("aliases")
    if login_shell:
        default_selected.append("login_shell")

    choices = [
        create_choice(
            title=description,
            value=name,
            checked=name in default_selected,
        )
        for name, description in ZSH_SETUP_OPTION_CANDIDATES
    ]
    selected = ask_checkbox_with_controls(
        "Select zsh setup options",
        choices=choices,
        default_values=default_selected,
        instruction="(Use arrow keys to move, <space> to toggle, <a> to toggle all, <enter> to confirm)",
        select_all_label="Select all setup options",
    )
    if selected == BACK_VALUE:
        raise click.Abort()
    selected_set = set(selected or [])
    return (
        "omz" in selected_set,
        "aliases" in selected_set,
        "login_shell" in selected_set,
    )


def render_zsh_aliases(include_quicksetup: bool = True, include_chattool: bool = True) -> str:
    lines = [ZSH_ALIASES_BEGIN, "# Managed by chattool setup zsh."]
    if include_quicksetup:
        lines.append(QUICKSETUP_ALIAS_BLOCK.rstrip("\n"))
    if include_chattool:
        lines.append("# ChatTool aliases")
        for key, command in ALIAS_MAP.items():
            lines.append(f"alias {key}='{command}'")
    lines.append(ZSH_ALIASES_END)
    return "\n".join(lines) + "\n"


def render_alias_source_block() -> str:
    return "\n".join(
        [
            ZSH_ALIASES_SOURCE_BEGIN,
            "# Load aliases managed by chattool setup zsh.",
            'if [ -f "$HOME/.zsh_aliases" ]; then source "$HOME/.zsh_aliases"; fi',
            ZSH_ALIASES_SOURCE_END,
        ]
    ) + "\n"


def render_login_shell_block(zsh_bin: str | None = None) -> str:
    zsh_bin = zsh_bin or "$(command -v zsh)"
    return "\n".join(
        [
            ZSH_LOGIN_BEGIN,
            "# Start login shells in zsh when bash_profile is used.",
            f'exec {zsh_bin} -l',
            ZSH_LOGIN_END,
        ]
    ) + "\n"


def _ensure_required_command(command_name: str, package_name: str) -> None:
    command_path = shutil.which(command_name)
    if command_path:
        click.echo(f"{command_name} already installed: {command_path}")
        return

    install_command = f"sudo apt install {package_name} -y"
    logger.error("%s not found", command_name)
    click.echo(f"{command_name} not found.", err=True)
    click.echo(f"Please install it first: {install_command}", err=True)
    raise click.Abort()


def _clone_if_missing(path: Path, repo: str, label: str, depth: int | None = None) -> None:
    if path.exists():
        click.echo(f"{label} already exists: {path}")
        return
    command = ["git", "clone"]
    if depth:
        command.extend(["--depth", str(depth)])
    command.extend([repo, str(path)])
    logger.info("Cloning %s into %s", label, path)
    _ensure_success(_run(command), f"Clone {label}")


def _ensure_omz(zshrc: Path, selected_plugins: list[str]) -> None:
    home = Path.home()
    omz_dir = home / ".oh-my-zsh"
    custom_dir = omz_dir / "custom"
    _clone_if_missing(omz_dir, OMZ_REPO, "oh-my-zsh")

    template = omz_dir / "templates" / "zshrc.zsh-template"
    if not zshrc.exists() and template.exists():
        zshrc.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    elif not zshrc.exists():
        zshrc.write_text('export ZSH="$HOME/.oh-my-zsh"\n', encoding="utf-8")

    for plugin in selected_plugins:
        repo = PLUGIN_REPOS.get(plugin)
        if repo:
            _clone_if_missing(custom_dir / "plugins" / plugin, repo, plugin)
    _clone_if_missing(custom_dir / "themes" / "powerlevel10k", P10K_REPO, "powerlevel10k", depth=1)

    _upsert_line(zshrc, r"^export ZSH=", 'export ZSH="$HOME/.oh-my-zsh"')
    _upsert_line(zshrc, r"^plugins=", f"plugins=({' '.join(selected_plugins)})")
    _upsert_line(zshrc, r"^ZSH_THEME=", f'ZSH_THEME="{P10K_THEME}"')
    _upsert_line(
        zshrc,
        r"^#?\s*zstyle ':omz:update' mode",
        "zstyle ':omz:update' mode disabled  # disable automatic updates",
    )
    content = zshrc.read_text(encoding="utf-8")
    with zshrc.open("a", encoding="utf-8") as file:
        if "oh-my-zsh.sh" not in content:
            file.write('[ -s "$ZSH/oh-my-zsh.sh" ] && source "$ZSH/oh-my-zsh.sh"\n')
        if "autoload -U compinit && compinit" not in content:
            file.write("autoload -U compinit && compinit\n")


def setup_zsh(
    interactive=None,
    install_omz=True,
    aliases=True,
    login_shell=True,
    log_level="INFO",
):
    _configure_logger(log_level)
    usage = "Usage: chattool setup zsh [--no-omz] [--no-aliases] [--login-shell/--no-login-shell] [-i|-I]"
    interactive, can_prompt, force_interactive, _, _ = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=False,
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)
    prompt_enabled = bool(force_interactive and can_prompt)

    if os.name != "posix":
        click.echo("setup zsh only supports Unix-like systems.", err=True)
        raise click.Abort()

    logger.info("Start zsh setup")
    zshrc = Path.home() / ".zshrc"
    aliases_path = Path.home() / ".zsh_aliases"

    if prompt_enabled:
        install_omz, aliases, login_shell = select_zsh_setup_options_interactively(
            install_omz=install_omz,
            aliases=aliases,
            login_shell=login_shell,
        )
        selected_options = []
        if install_omz:
            selected_options.append("oh-my-zsh")
        if aliases:
            selected_options.append("aliases")
        if login_shell:
            selected_options.append("login shell")
        click.echo("Selected zsh setup options: " + (", ".join(selected_options) or "none"))

    selected_plugins = list(DEFAULT_OMZ_PLUGINS)
    if install_omz:
        # Match QuickSetup's dependency order: git is needed before cloning omz.
        _ensure_required_command("git", "git")
    _ensure_required_command("zsh", "zsh")

    if install_omz:
        if prompt_enabled:
            selected_plugins = select_omz_plugins_interactively(selected_plugins)
        if selected_plugins:
            click.echo("Selected oh-my-zsh plugins: " + ", ".join(selected_plugins))
        else:
            click.echo("Selected oh-my-zsh plugins: none")
        _ensure_omz(zshrc, selected_plugins=selected_plugins)

    if aliases:
        alias_block = render_zsh_aliases()
        source_block = render_alias_source_block()
        _replace_managed_block(aliases_path, ZSH_ALIASES_BEGIN, ZSH_ALIASES_END, alias_block)
        _replace_managed_block(zshrc, ZSH_ALIASES_SOURCE_BEGIN, ZSH_ALIASES_SOURCE_END, source_block)
        click.echo(f"Updated aliases: {aliases_path}")
        click.echo(f"Ensured alias source in: {zshrc}")

    if login_shell:
        block = render_login_shell_block(shutil.which("zsh"))
        bash_profile = Path.home() / ".bash_profile"
        _replace_managed_block(bash_profile, ZSH_LOGIN_BEGIN, ZSH_LOGIN_END, block)
        click.echo(f"Ensured zsh login handoff in: {bash_profile}")

    click.echo("zsh setup completed.")
    if aliases:
        click.echo("Run: source ~/.zshrc")
