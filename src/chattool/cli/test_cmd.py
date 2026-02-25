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
    # Load env file first to ensure values are populated?
    # Usually the app loads env at startup.
    # But BaseEnvConfig.test() instantiates clients which usually load env.
    # Let's check if we need to load env explicitly here.
    # BaseEnvConfig.load_all(".env") ? 
    # The original test_cmd didn't load env explicitly, assuming it's loaded or handled by libraries.
    # But usually cli entry point loads env.
    # I'll assume environment is set up.

    config_cls = BaseEnvConfig.get_config_by_alias(target)
    
    if config_cls:
        config_cls.test()
    else:
        click.echo(f"❌ Unknown target: {target}", err=True)
        click.echo("Available targets:")
        for cls in BaseEnvConfig._registry:
            aliases = ", ".join(cls._aliases)
            click.echo(f"  - {cls._title}: {aliases}")
