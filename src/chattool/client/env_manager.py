import click
from chattool.utils import BaseEnvConfig
from chattool.const import CHATTOOL_ENV_FILE
from chattool import __version__

@click.group(name='env')
def cli():
    """Manage configuration environment variables."""
    pass

@cli.command()
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode to set values.')
def init(interactive):
    """Initialize or update the .env configuration file."""
    
    if interactive:
        click.echo("Starting interactive configuration...")
        
        # Iterate through all registered config classes
        for config_cls in BaseEnvConfig._registry:
            click.echo(f"\n[{config_cls._title}]")
            
            # Iterate through fields
            for name, field in config_cls.get_fields().items():
                prompt_text = f"{name}"
                if field.desc:
                    prompt_text += f" ({field.desc})"
                
                # Determine default value for prompt
                default_val = field.value if field.value is not None else field.default
                
                # Ask user for input
                new_val = click.prompt(
                    prompt_text,
                    default=default_val if default_val is not None else "",
                    show_default=True,
                    type=str
                )
                
                # Update field value
                if new_val:
                     field.value = new_val
    
    # Save to file
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
    
    # Update in memory
    BaseEnvConfig.set(key, value)
    
    # Save to file
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

@cli.command(name='list')
def list_env():
    """List all configuration values."""
    BaseEnvConfig.print_config()

@cli.command(name='unset')
@click.argument('key')
def unset_env(key):
    """Unset a configuration value."""
    # Update in memory
    BaseEnvConfig.set(key, "")
    
    # Save to file
    BaseEnvConfig.save_env_file(str(CHATTOOL_ENV_FILE), __version__)
    click.echo(f"Unset {key}")

if __name__ == '__main__':
    cli()
