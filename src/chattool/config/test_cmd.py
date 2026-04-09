import click
from chattool.interaction import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    resolve_command_inputs,
)
from chattool.config.elements import BaseEnvConfig

# Ensure all configs are registered
import chattool.config.main

__test__ = False


TEST_TARGET_SCHEMA = CommandSchema(
    name="chatenv-test-target",
    fields=(CommandField("target", prompt="target", required=True),),
)


def get_all_aliases():
    aliases = []
    for cls in BaseEnvConfig._registry:
        aliases.extend(cls._aliases)
    return aliases


@click.command(name="test")
@click.option("--target", "-t", required=False, help="Target service to test.")
@add_interactive_option
def test_cmd(target, interactive):
    """Test the configuration for a specific service.

    Supported targets are defined in the configuration classes.
    """
    inputs = resolve_command_inputs(
        schema=TEST_TARGET_SCHEMA,
        provided={"target": target},
        interactive=interactive,
        usage="Usage: chatenv test --target TEXT [-i|-I]",
    )
    target = inputs["target"]

    config_cls = BaseEnvConfig.get_config_by_alias(target)

    if config_cls:
        config_cls.test()
    else:
        click.echo(f"❌ Unknown target: {target}", err=True)
        click.echo("Available targets:")
        for cls in BaseEnvConfig._registry:
            aliases = ", ".join(cls._aliases)
            click.echo(f"  - {cls._title}: {aliases}")
