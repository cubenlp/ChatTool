import click
from chattool.config.elements import BaseEnvConfig
# Ensure all configs are registered
import chattool.config.main

def get_all_aliases():
    aliases = []
    for cls in BaseEnvConfig._registry:
        aliases.extend(cls._aliases)
    return aliases

@click.command(name='test')
@click.option('--target', '-t', required=True, help='Target service to test.')
def test_cmd(target):
    """Test the configuration for a specific service.
    
    Supported targets are defined in the configuration classes.
    """
    config_cls = BaseEnvConfig.get_config_by_alias(target)
    
    if config_cls:
        config_cls.test()
    else:
        click.echo(f"❌ Unknown target: {target}", err=True)
        click.echo("Available targets:")
        for cls in BaseEnvConfig._registry:
            aliases = ", ".join(cls._aliases)
            click.echo(f"  - {cls._title}: {aliases}")
