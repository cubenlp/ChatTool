import click
import shutil
import os

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

    if interactive:
        click.echo("Starting interactive configuration...")
        
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
