from __future__ import annotations

import click
from click.testing import CliRunner

from chattool.chatstyle.constants import INTERACTIVE_OPTION_HELP
from chattool.chatstyle.mask import mask_secret as chatstyle_mask_secret
from chattool.interaction import (
    BACK_VALUE,
    CommandField,
    CommandSchema,
    add_interactive_option,
    ask_text,
    create_choice,
)
from chattool.utils import mask_secret as utils_mask_secret


def test_chatstyle_keeps_interaction_compatibility_exports():
    from chattool.chatstyle.prompt import ask_text as chatstyle_ask_text

    assert ask_text is chatstyle_ask_text
    assert BACK_VALUE == "__BACK__"

    choice = create_choice("Demo", "demo")
    assert getattr(choice, "value", None) == "demo" or choice["value"] == "demo"

    schema = CommandSchema(
        name="demo",
        fields=(CommandField("name", prompt="name", required=True),),
    )
    assert schema.fields[0].name == "name"


def test_chatstyle_interactive_help_constant_is_used():
    @click.command()
    @add_interactive_option
    def demo(interactive):
        click.echo(interactive)

    result = CliRunner().invoke(demo, ["--help"])

    assert result.exit_code == 0
    assert demo.params[0].help == INTERACTIVE_OPTION_HELP
    assert "-i" in result.output
    assert "-I" in result.output


def test_chatstyle_mask_secret_matches_legacy_utils():
    value = "sk-1234567890abcdef"

    assert utils_mask_secret(value) == chatstyle_mask_secret(value)
    assert chatstyle_mask_secret("ab") == "**"
