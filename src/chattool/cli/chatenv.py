import click
import shutil
import os
import sys
import questionary

from chattool.config import BaseEnvConfig
from chattool.const import CHATTOOL_ENV_FILE, CHATTOOL_ENV_DIR
from chattool import __version__
from chattool.utils import mask_secret

from .test_cmd import test_cmd

@click.group(name='chatenv')
def cli():
    """Manage configuration environment variables and profiles."""
    if not CHATTOOL_ENV_DIR.exists():
        CHATTOOL_ENV_DIR.mkdir(parents=True)

@cli.command(name='list')
def profiles():
    """List all available environment profiles."""
    configs = list(CHATTOOL_ENV_DIR.glob('*.env'))
    if configs:
        click.echo("Available profiles:")
        for config in configs:
            click.echo(f"- {config.stem}")
    else:
        click.echo(f"No profiles found in {CHATTOOL_ENV_DIR}")

def _resolve_config_types(config_types):
    """Resolve -t filter to matching config classes. Returns None if no filter."""
    if not config_types:
        return None
    normalized = [t.lower() for t in config_types]
    matched = [
        cls for cls in BaseEnvConfig._registry
        if cls._title.lower() in normalized
        or any(a.lower() in normalized for a in getattr(cls, '_aliases', []))
    ]
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
        if name in ("OpenAIConfig", "AzureConfig", "DeepSeekConfig", "SiliconFlowConfig"):
            groups["Model"].append(cfg)
        elif name in ("AliyunConfig", "TencentConfig"):
            groups["DNS"].append(cfg)
        elif name in ("TongyiConfig", "HuggingFaceConfig", "LiblibConfig", "BingConfig"):
            groups["Image"].append(cfg)
        else:
            groups["Other"].append(cfg)
    return groups


def _get_style():
    """Custom style for questionary."""
    return questionary.Style([
        ('qmark', 'fg:#5f819d bold'),       # token in front of the question
        ('question', 'bold'),               # question text
        ('answer', 'fg:#f44336 bold'),      # submitted answer text
        ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox
        ('highlighted', 'fg:#673ab7 bold'), # highlighted option in select and checkbox
        ('selected', 'fg:#cc545a'),         # selected checkbox
        ('separator', 'fg:#cc545a'),        # separator in lists
        ('instruction', 'fg:#808080'),      # user instructions for select, rawselect, checkbox
        ('text', ''),                       # plain text
        ('disabled', 'fg:#858585 italic')   # disabled choices for select and checkbox
    ])


def _configure_provider(config_cls, style):
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
            
            new_val = questionary.password(message, style=style).ask()
            if new_val:
                field.value = new_val
        else:
            new_val = questionary.text(
                prompt_text,
                default=str(default_val) if default_val is not None else "",
                style=style
            ).ask()
            if new_val:
                field.value = new_val


def _interactive_config_loop(grouped_configs):
    """Main loop for interactive configuration using questionary."""
    style = _get_style()
    
    while True:
        # Main Menu
        main_choices = []
        for section, configs in grouped_configs.items():
            if configs:
                main_choices.append(section)
        
        main_choices.append(questionary.Separator())
        main_choices.append("Save & Exit")
        main_choices.append("Exit without Saving")
        
        selected_section = questionary.select(
            "Select a category to configure (Arrow keys to move, Enter to select):",
            choices=main_choices,
            style=style,
            use_arrow_keys=True,
        ).ask()
        
        if selected_section == "Save & Exit":
            BaseEnvConfig.save_env_file(str(CHATTOOL_ENV_FILE), __version__)
            click.echo(f"Configuration saved to {CHATTOOL_ENV_FILE}")
            break
        elif selected_section == "Exit without Saving":
            if questionary.confirm("Are you sure you want to exit without saving changes?", default=False, style=style).ask():
                break
            continue
        elif selected_section is None:
             break

        # Sub Menu
        while True:
            configs = grouped_configs[selected_section]
            sub_choices = []
            for cfg in configs:
                aliases = getattr(cfg, '_aliases', [])
                alias_text = f" ({', '.join(aliases)})" if aliases else ""
                sub_choices.append(questionary.Choice(
                    title=f"{cfg._title}{alias_text}",
                    value=cfg
                ))
            
            sub_choices.append(questionary.Separator())
            sub_choices.append(questionary.Choice(title="Back", value="Back"))
            
            selected_config = questionary.select(
                f"[{selected_section}] Select a provider to configure:",
                choices=sub_choices,
                style=style,
                use_arrow_keys=True,
            ).ask()
            
            if selected_config == "Back" or selected_config is None:
                break
            
            # Configure Provider
            _configure_provider(selected_config, style)


@cli.command(name='cat')
@click.argument('name', required=False)
@click.option('--no-mask', is_flag=True, help='Show values in plain text without masking.')
@click.option('--type', '-t', 'config_types', multiple=True,
              help='Filter configuration types (e.g. openai, feishu, aliyun).')
def cat_env(name, no_mask, config_types):
    """Print the content of an environment profile or current .env.

    \b
    Examples:
      chatenv cat                # show all
      chatenv cat -t feishu      # only show Feishu config
      chatenv cat -t openai -t feishu
    """
    if name:
        config_path = CHATTOOL_ENV_DIR / f'{name}.env'
    else:
        config_path = CHATTOOL_ENV_FILE

    if not config_path.exists():
        click.echo(f"Error: Environment file '{config_path}' not found.", err=True)
        return

    # Build lookup sets
    sensitive_keys = set()
    for config_cls in BaseEnvConfig._registry:
        for _, field in config_cls.get_fields().items():
            if field.is_sensitive:
                sensitive_keys.add(field.env_key)

    # If -t is specified, only show keys belonging to those configs
    filter_keys = None
    if config_types:
        matched = _resolve_config_types(config_types)
        if not matched:
            click.echo(f"No configuration types matched: {', '.join(config_types)}")
            click.echo("Available types (and aliases):")
            for cls in BaseEnvConfig._registry:
                aliases = getattr(cls, '_aliases', [])
                alias_str = f" ({', '.join(aliases)})" if aliases else ""
                click.echo(f"  - {cls._title}{alias_str}")
            return
        filter_keys = set()
        for cls in matched:
            for _, field in cls.get_fields().items():
                filter_keys.add(field.env_key)

    content = config_path.read_text()
    if no_mask and filter_keys is None:
        click.echo(content)
        return

    for line in content.splitlines():
        line_strip = line.strip()

        if not line_strip or line_strip.startswith('#'):
            if filter_keys is None:
                click.echo(line)
            continue

        if '=' not in line:
            if filter_keys is None:
                click.echo(line)
            continue

        key, value = line.split('=', 1)
        key = key.strip()

        if filter_keys is not None and key not in filter_keys:
            continue

        if no_mask or key not in sensitive_keys:
            click.echo(line)
        else:
            val_part = value.strip()
            quote = ''
            raw_val = val_part
            if len(val_part) >= 2:
                if (val_part.startswith("'") and val_part.endswith("'")) or \
                   (val_part.startswith('"') and val_part.endswith('"')):
                    quote = val_part[0]
                    raw_val = val_part[1:-1]
            masked = mask_secret(raw_val)
            click.echo(f"{key}={quote}{masked}{quote}")

@cli.command(name='save')
@click.argument('name')
def save_env(name):
    """Save the current .env configuration as a profile."""
    if not CHATTOOL_ENV_FILE.exists():
        click.echo("Error: No active .env file to save.", err=True)
        return

    target_path = CHATTOOL_ENV_DIR / f'{name}.env'
    if target_path.exists():
        click.confirm(f"Profile '{name}' already exists. Overwrite?", abort=True)
    
    shutil.copy(CHATTOOL_ENV_FILE, target_path)
    click.echo(f"Saved current configuration to profile '{name}'")

@cli.command(name='use')
@click.argument('name')
def use_env(name):
    """Activate an environment profile."""
    source_path = CHATTOOL_ENV_DIR / f'{name}.env'
    if not source_path.exists():
        click.echo(f"Error: Profile '{name}' not found.", err=True)
        return
    
    shutil.copy(source_path, CHATTOOL_ENV_FILE)
    click.echo(f"Activated profile '{name}'")

@cli.command(name='delete')
@click.argument('name')
def delete_env(name):
    """Delete an environment profile."""
    target_path = CHATTOOL_ENV_DIR / f'{name}.env'
    if not target_path.exists():
        click.echo(f"Error: Profile '{name}' not found.", err=True)
        return
    
    os.remove(target_path)
    click.echo(f"Deleted profile '{name}'")

@cli.command(name='init')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode to set values.')
@click.option('--type', '-t', 'config_types', multiple=True, help='Filter configuration types (case-insensitive title or alias match).')
def init(interactive, config_types):
    """Initialize or update the .env configuration file.
    
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
    - Liblib: liblib
    - Bing: bing
    """
    
    target_configs = BaseEnvConfig._registry
    if config_types:
        target_configs = _resolve_config_types(config_types)
        if not target_configs:
            click.echo(f"No configuration types matched: {', '.join(config_types)}")
            click.echo("Available types (and aliases):")
            for cls in BaseEnvConfig._registry:
                aliases = getattr(cls, '_aliases', [])
                alias_str = f" ({', '.join(aliases)})" if aliases else ""
                click.echo(f"  - {cls._title}{alias_str}")
            return

    # Load existing values from file to serve as defaults
    if CHATTOOL_ENV_FILE.exists():
        BaseEnvConfig.load_all(CHATTOOL_ENV_FILE)

    if not interactive:
        interactive = True

    if interactive:
        click.echo("Starting interactive configuration...")
        use_questionary = sys.stdin.isatty() and sys.stdout.isatty()
        
        if use_questionary:
            style = _get_style()
            if not config_types:
                grouped = _group_configs(target_configs)
                _interactive_config_loop(grouped)
                return
            else:
                # Linear config for specific types
                for config_cls in target_configs:
                    _configure_provider(config_cls, style)
                
                BaseEnvConfig.save_env_file(str(CHATTOOL_ENV_FILE), __version__)
                click.echo(f"Configuration saved to {CHATTOOL_ENV_FILE}")
                return

        # Fallback for non-questionary environment (pure click)
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
                    aliases = getattr(config_cls, '_aliases', [])
                    alias_text = f" ({', '.join(aliases)})" if aliases else ""
                    if click.confirm(f"Configure {config_cls._title}{alias_text}", default=False):
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
    
    BaseEnvConfig.save_env_file(str(CHATTOOL_ENV_FILE), __version__)
    click.echo(f"Configuration saved to {CHATTOOL_ENV_FILE}")

@cli.command(name='set')
@click.argument('key_value')
def set_env(key_value):
    """Set a configuration value (KEY=VALUE)."""
    if '=' not in key_value:
        click.echo("Error: Invalid format. Use KEY=VALUE", err=True)
        return

    key, value = key_value.split('=', 1)
    key = key.strip()
    value = value.strip()
    
    BaseEnvConfig.set(key, value)
    
    BaseEnvConfig.save_env_file(str(CHATTOOL_ENV_FILE), __version__)
    click.echo(f"Set {key}={value}")

@cli.command(name='get')
@click.argument('key')
def get_env(key):
    """Get a configuration value."""
    values = BaseEnvConfig.get_all_values()
    if key in values:
        val = values[key]
        click.echo(val if val is not None else "")
    else:
        click.echo(f"Error: Key '{key}' not found", err=True)

@cli.command(name='unset')
@click.argument('key')
def unset_env(key):
    """Unset a configuration value."""
    BaseEnvConfig.set(key, "")
    BaseEnvConfig.save_env_file(str(CHATTOOL_ENV_FILE), __version__)
    click.echo(f"Unset {key}")

cli.add_command(test_cmd)

if __name__ == '__main__':
    cli()
