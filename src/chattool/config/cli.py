import click
import shutil
import os
import dotenv

from chattool.interaction import (
    BACK_VALUE,
    ask_confirm,
    ask_select,
    ask_text,
    create_choice,
    get_separator,
    is_interactive_available,
)
from chattool.config import BaseEnvConfig
from chattool.interaction import install_cli_warning_filters
from chattool.const import CHATTOOL_ENV_FILE, CHATTOOL_ENV_DIR
from chattool.utils import mask_secret

from .test_cmd import test_cmd

install_cli_warning_filters()


@click.group(name="chatenv")
def cli():
    """Manage configuration environment variables and profiles."""
    if not CHATTOOL_ENV_DIR.exists():
        CHATTOOL_ENV_DIR.mkdir(parents=True)


def _reload_runtime_config() -> None:
    BaseEnvConfig.load_all(CHATTOOL_ENV_DIR, legacy_env_file=CHATTOOL_ENV_FILE)


def _require_single_config(config_types, action: str):
    if not config_types:
        raise click.ClickException(
            f"{action} requires --type/-t to select exactly one config type."
        )
    matched = _resolve_config_types(config_types)
    if not matched:
        click.echo(f"No configuration types matched: {', '.join(config_types)}")
        click.echo("Available types (and aliases):")
        for cls in BaseEnvConfig._registry:
            aliases = getattr(cls, "_aliases", [])
            alias_str = f" ({', '.join(aliases)})" if aliases else ""
            click.echo(f"  - {cls._title}{alias_str}")
        raise click.Abort()
    if len(matched) != 1:
        names = ", ".join(config_cls.get_storage_name() for config_cls in matched)
        raise click.ClickException(
            f"{action} requires exactly one config type. Matched: {names}"
        )
    return matched[0]


def _select_single_config_interactive(action: str):
    choices = []
    for config_cls in BaseEnvConfig._registry:
        aliases = getattr(config_cls, "_aliases", [])
        alias_text = f" ({', '.join(aliases)})" if aliases else ""
        choices.append(
            create_choice(
                title=f"{config_cls.get_storage_name()}{alias_text}",
                value=config_cls,
            )
        )

    selected = ask_select(
        f"Select one config type for {action}:",
        choices=choices,
    )
    if selected == BACK_VALUE:
        raise click.Abort()
    return selected


def _resolve_single_config_for_profile_action(config_types, action: str):
    if config_types:
        return _require_single_config(config_types, action)
    if is_interactive_available():
        return _select_single_config_interactive(action)
    raise click.ClickException(f"{action} requires --type/-t outside interactive mode.")


def _normalize_profile_name(name: str) -> str:
    profile_name = str(name).strip()
    if not profile_name:
        raise click.ClickException("Profile name cannot be empty.")
    return profile_name.removesuffix(".env")


def _write_config_files(configs):
    CHATTOOL_ENV_DIR.mkdir(parents=True, exist_ok=True)
    for config_cls in configs:
        config_dir = config_cls.get_storage_dir(CHATTOOL_ENV_DIR)
        config_dir.mkdir(parents=True, exist_ok=True)
        config_cls.get_active_env_file(CHATTOOL_ENV_DIR).write_text(
            config_cls.render_env_file(),
            encoding="utf-8",
        )


def _render_field_line(field, no_mask: bool) -> str:
    value = "" if field.value is None else str(field.value)
    if field.is_sensitive and not no_mask:
        value = mask_secret(value)
    return f"{field.env_key}='{value}'"


@cli.command(name="list")
@click.option(
    "--type",
    "-t",
    "config_types",
    multiple=True,
    help="Filter configuration types (e.g. openai, feishu, aliyun).",
)
def profiles(config_types):
    """List available environment profiles grouped by config type."""
    matched = (
        _resolve_config_types(config_types) if config_types else BaseEnvConfig._registry
    )
    if config_types and not matched:
        click.echo(f"No configuration types matched: {', '.join(config_types)}")
        return
    found = False
    for config_cls in matched:
        config_dir = config_cls.get_storage_dir(CHATTOOL_ENV_DIR)
        profiles = (
            sorted(
                path.name for path in config_dir.glob("*.env") if path.name != ".env"
            )
            if config_dir.exists()
            else []
        )
        if not profiles:
            continue
        found = True
        click.echo(f"[{config_cls.get_storage_name()}]")
        for profile in profiles:
            click.echo(f"- {profile}")
    if not found:
        click.echo(f"No profiles found under {CHATTOOL_ENV_DIR}")


def _resolve_config_types(config_types):
    """Resolve -t filter to matching config classes. Returns None if no filter."""
    if not config_types:
        return None
    normalized = [t.lower() for t in config_types]

    matched = []

    for cls in BaseEnvConfig._registry:
        is_match = False

        for t in normalized:
            # Check title (case-insensitive prefix)
            if cls._title.lower().startswith(t):
                is_match = True

            # Check aliases (case-insensitive prefix)
            if not is_match:
                aliases = getattr(cls, "_aliases", [])
                for alias in aliases:
                    if alias.lower().startswith(t):
                        is_match = True
                        break

            if is_match:
                break

        if is_match:
            matched.append(cls)

    return matched


def _group_configs(configs):
    groups = {
        "Model": [],
        "DNS": [],
        "Image": [],
        "Other": [],
    }
    for cfg in configs:
        name = cfg.__name__
        if name in ("OpenAIConfig", "AzureConfig", "SiliconFlowConfig"):
            groups["Model"].append(cfg)
        elif name in ("AliyunConfig", "TencentConfig"):
            groups["DNS"].append(cfg)
        elif name in (
            "TongyiConfig",
            "HuggingFaceConfig",
            "PollinationsConfig",
            "LiblibConfig",
        ):
            groups["Image"].append(cfg)
        else:
            groups["Other"].append(cfg)
    return groups


def _configure_provider(config_cls):
    """Interactively configure a single provider."""
    click.echo(f"\nConfiguring {config_cls._title}...")
    for name, field in config_cls.get_fields().items():
        prompt_text = f"{name}"
        if field.desc:
            prompt_text += f" ({field.desc})"

        default_val = field.value if field.value is not None else field.default

        if field.is_sensitive:
            hint = mask_secret(default_val) if default_val else ""
            message = f"{prompt_text}"
            if hint:
                message += f" [current: {hint}]"
            message += " (leave blank to keep current)"

            new_val = ask_text(message, password=True)
            if new_val == BACK_VALUE:
                return False
            if new_val:
                field.value = new_val
        else:
            new_val = ask_text(
                prompt_text, default=str(default_val) if default_val is not None else ""
            )
            if new_val == BACK_VALUE:
                return False
            if new_val:
                field.value = new_val
    return True


def _interactive_config_loop(grouped_configs):
    """Main loop for interactive configuration using shared tui helpers."""
    while True:
        # Main Menu
        main_choices = []
        for section, configs in grouped_configs.items():
            if configs:
                main_choices.append(section)

        main_choices.append(get_separator())
        main_choices.append("Save & Exit")
        main_choices.append("Exit without Saving")

        selected_section = ask_select(
            "Select a category to configure:", choices=main_choices
        )

        if selected_section == "Save & Exit":
            _write_config_files(BaseEnvConfig._registry)
            click.echo(f"Configuration saved to {CHATTOOL_ENV_DIR}")
            break
        elif selected_section == "Exit without Saving":
            if ask_confirm(
                "Are you sure you want to exit without saving changes?", default=False
            ):
                break
            continue
        elif selected_section == BACK_VALUE:
            continue

        # Sub Menu
        while True:
            configs = grouped_configs[selected_section]
            sub_choices = []
            for cfg in configs:
                aliases = getattr(cfg, "_aliases", [])
                alias_text = f" ({', '.join(aliases)})" if aliases else ""
                sub_choices.append(
                    create_choice(title=f"{cfg._title}{alias_text}", value=cfg)
                )

            sub_choices.append(get_separator())
            sub_choices.append(create_choice(title="Back", value="Back"))

            selected_config = ask_select(
                f"[{selected_section}] Select a provider to configure:",
                choices=sub_choices,
            )

            if selected_config == "Back" or selected_config == BACK_VALUE:
                break

            # Configure Provider
            _configure_provider(selected_config)


@cli.command(name="cat")
@click.argument("name", required=False)
@click.option(
    "--no-mask", is_flag=True, help="Show values in plain text without masking."
)
@click.option(
    "--type",
    "-t",
    "config_types",
    multiple=True,
    help="Filter configuration types (e.g. openai, feishu, aliyun).",
)
def cat_env(name, no_mask, config_types):
    """Print effective config values or a typed env profile.

    \b
    Examples:
      chatenv cat                # show all
      chatenv cat -t feishu      # only show Feishu config
      chatenv cat -t openai -t feishu
    """
    matched = (
        _resolve_config_types(config_types) if config_types else BaseEnvConfig._registry
    )
    if config_types and not matched:
        click.echo(f"No configuration types matched: {', '.join(config_types)}")
        click.echo("Available types (and aliases):")
        for cls in BaseEnvConfig._registry:
            aliases = getattr(cls, "_aliases", [])
            alias_str = f" ({', '.join(aliases)})" if aliases else ""
            click.echo(f"  - {cls._title}{alias_str}")
        return

    if name:
        config_cls = _require_single_config(config_types, "cat")
        profile_path = config_cls.get_profile_env_file(CHATTOOL_ENV_DIR, name)
        if not profile_path.exists():
            click.echo(f"Error: Environment file '{profile_path}' not found.", err=True)
            return
        config_cls.load_from_dict(dotenv.dotenv_values(profile_path))
        for _, field in config_cls.get_fields().items():
            click.echo(_render_field_line(field, no_mask))
        return

    _reload_runtime_config()
    for index, config_cls in enumerate(matched):
        if len(matched) > 1:
            if index:
                click.echo("")
            click.echo(f"# {config_cls.get_storage_name()}")
        for _, field in config_cls.get_fields().items():
            click.echo(_render_field_line(field, no_mask))


@cli.command(name="save")
@click.argument("name")
@click.option(
    "--type",
    "-t",
    "config_types",
    multiple=True,
    help="Target exactly one configuration type.",
)
def save_env(name, config_types):
    """Save the current active config for one type as a profile."""
    config_cls = _resolve_single_config_for_profile_action(config_types, "save")
    name = _normalize_profile_name(name)
    target_path = config_cls.get_profile_env_file(CHATTOOL_ENV_DIR, name)
    if target_path.exists():
        click.confirm(f"Profile '{name}' already exists. Overwrite?", abort=True)

    _reload_runtime_config()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(config_cls.render_env_file(), encoding="utf-8")
    click.echo(
        f"Saved current {config_cls.get_storage_name()} configuration to profile '{target_path.name}'"
    )


@cli.command(name="new")
@click.argument("name", required=False)
@click.option(
    "--type",
    "-t",
    "config_types",
    multiple=True,
    help="Target exactly one configuration type.",
)
def new_env(name, config_types):
    """Create a new typed profile without changing the active config."""
    config_cls = _resolve_single_config_for_profile_action(config_types, "new")
    prompt_for_values = False

    if not name:
        if not is_interactive_available():
            raise click.ClickException(
                "new requires a profile name outside interactive mode."
            )
        name = ask_text("New profile name")
        if name == BACK_VALUE:
            raise click.Abort()
        prompt_for_values = True

    name = _normalize_profile_name(name)
    target_path = config_cls.get_profile_env_file(CHATTOOL_ENV_DIR, name)
    if target_path.exists():
        click.confirm(f"Profile '{name}' already exists. Overwrite it?", abort=True)

    _reload_runtime_config()
    if prompt_for_values and not _configure_provider(config_cls):
        raise click.Abort()

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(config_cls.render_env_file(), encoding="utf-8")
    _reload_runtime_config()

    click.echo(f"Created {config_cls.get_storage_name()} profile '{target_path.name}'")


@cli.command(name="use")
@click.argument("name")
@click.option(
    "--type",
    "-t",
    "config_types",
    multiple=True,
    help="Target exactly one configuration type.",
)
def use_env(name, config_types):
    """Activate a profile for one config type."""
    config_cls = _resolve_single_config_for_profile_action(config_types, "use")
    name = _normalize_profile_name(name)
    source_path = config_cls.get_profile_env_file(CHATTOOL_ENV_DIR, name)
    if not source_path.exists():
        click.echo(f"Error: Profile '{name}' not found.", err=True)
        return

    target_path = config_cls.get_active_env_file(CHATTOOL_ENV_DIR)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source_path, target_path)
    _reload_runtime_config()
    click.echo(
        f"Activated {config_cls.get_storage_name()} profile '{source_path.name}'"
    )


@cli.command(name="delete")
@click.argument("name")
@click.option(
    "--type",
    "-t",
    "config_types",
    multiple=True,
    help="Target exactly one configuration type.",
)
def delete_env(name, config_types):
    """Delete a profile for one config type."""
    config_cls = _resolve_single_config_for_profile_action(config_types, "delete")
    name = _normalize_profile_name(name)
    target_path = config_cls.get_profile_env_file(CHATTOOL_ENV_DIR, name)
    if not target_path.exists():
        click.echo(f"Error: Profile '{name}' not found.", err=True)
        return

    os.remove(target_path)
    click.echo(f"Deleted {config_cls.get_storage_name()} profile '{target_path.name}'")


@cli.command(name="init")
@click.option(
    "--interactive/--no-interactive",
    "-i/-I",
    default=None,
    help="Auto prompt by default, -i forces interactive, -I disables interactive.",
)
@click.option(
    "--type",
    "-t",
    "config_types",
    multiple=True,
    help="Filter configuration types (case-insensitive title or alias match).",
)
def init(interactive, config_types):
    """Initialize or update config env files.

    You can filter the configuration types using the -t/--type option.

    \b
    Supported aliases:
    - OpenAI: oai, openai
    - Azure: azure, az
    - Aliyun: ali, aliyun, alidns
    - Tencent: tencent, tx, tencent-dns
    - Zulip: zulip
    - Feishu: feishu, lark
    - Tongyi: tongyi, dashscope
    - HuggingFace: hf, huggingface
    - Pollinations: pollinations, poll
    - Liblib: liblib
    - SiliconFlow: siliconflow (Model & Image)
    """

    target_configs = BaseEnvConfig._registry
    if config_types:
        target_configs = _resolve_config_types(config_types)
        if not target_configs:
            click.echo(f"No configuration types matched: {', '.join(config_types)}")
            click.echo("Available types (and aliases):")
            for cls in BaseEnvConfig._registry:
                aliases = getattr(cls, "_aliases", [])
                alias_str = f" ({', '.join(aliases)})" if aliases else ""
                click.echo(f"  - {cls._title}{alias_str}")
            return

    if interactive is None:
        interactive = True

    if interactive:
        click.echo("Starting interactive configuration...")
        interactive_tui_available = is_interactive_available()

        if interactive_tui_available:
            if not config_types:
                grouped = _group_configs(target_configs)
                _interactive_config_loop(grouped)
                return
            else:
                # Linear config for specific types
                for config_cls in target_configs:
                    _configure_provider(config_cls)

                _write_config_files(target_configs)
                click.echo(f"Configuration saved to {CHATTOOL_ENV_DIR}")
                return

        # Fallback for non-interactive-tui environment (pure click)
        if not config_types:
            grouped = _group_configs(target_configs)
            selected_sections = []
            click.echo("\nSelect sections to configure:")
            for section, configs in grouped.items():
                if not configs:
                    continue
                if click.confirm(section, default=section == "Model"):
                    selected_sections.append(section)

            if not selected_sections:
                click.echo("No section selected. Nothing to update.")
                return

            selected_configs = []
            for section in selected_sections:
                click.echo(f"\n[{section}]")
                for config_cls in grouped[section]:
                    aliases = getattr(config_cls, "_aliases", [])
                    alias_text = f" ({', '.join(aliases)})" if aliases else ""
                    if click.confirm(
                        f"Configure {config_cls._title}{alias_text}", default=False
                    ):
                        selected_configs.append(config_cls)

            if not selected_configs:
                click.echo("No provider selected. Nothing to update.")
                return
            target_configs = selected_configs

        for config_cls in target_configs:
            click.echo(f"\n[{config_cls._title}]")

            for name, field in config_cls.get_fields().items():
                prompt_text = f"{name}"
                if field.desc:
                    prompt_text += f" ({field.desc})"

                default_val = field.value if field.value is not None else field.default

                if field.is_sensitive:
                    hint = mask_secret(default_val) if default_val else ""
                    if hint:
                        prompt_text += f" [{hint}]"
                    new_val = click.prompt(
                        prompt_text,
                        default="",
                        show_default=False,
                        hide_input=True,
                        type=str,
                    )
                    if new_val:
                        field.value = new_val
                else:
                    new_val = click.prompt(
                        prompt_text,
                        default=default_val if default_val is not None else "",
                        show_default=True,
                        type=str,
                    )
                    if new_val:
                        field.value = new_val

    _write_config_files(target_configs)
    click.echo(f"Configuration saved to {CHATTOOL_ENV_DIR}")


@cli.command(name="set")
@click.argument("key_value")
def set_env(key_value):
    """Set a configuration value (KEY=VALUE)."""
    if "=" not in key_value:
        click.echo("Error: Invalid format. Use KEY=VALUE", err=True)
        return

    key, value = key_value.split("=", 1)
    key = key.strip()
    value = value.strip()

    match = BaseEnvConfig.find_field(key)
    if match is None:
        click.echo(f"Error: Key '{key}' not found", err=True)
        return

    config_cls, _ = match
    BaseEnvConfig.set(key, value)
    _write_config_files([config_cls])
    click.echo(f"Set {key}={value}")


@cli.command(name="get")
@click.argument("key")
def get_env(key):
    """Get a configuration value."""
    _reload_runtime_config()
    match = BaseEnvConfig.find_field(key)
    if match is None:
        click.echo(f"Error: Key '{key}' not found", err=True)
        return
    _, field = match
    val = field.value
    click.echo(val if val is not None else "")


@cli.command(name="unset")
@click.argument("key")
def unset_env(key):
    """Unset a configuration value."""
    match = BaseEnvConfig.find_field(key)
    if match is None:
        click.echo(f"Error: Key '{key}' not found", err=True)
        return

    config_cls, _ = match
    BaseEnvConfig.set(key, "")
    _write_config_files([config_cls])
    click.echo(f"Unset {key}")


cli.add_command(test_cmd)

if __name__ == "__main__":
    cli()
