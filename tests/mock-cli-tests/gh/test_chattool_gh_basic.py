from click.testing import CliRunner

from chattool.client.main import cli
from chattool.setup.alias import ALIAS_MAP, render_alias_block


def test_chattool_no_longer_exposes_gh_command():
    runner = CliRunner()

    help_result = runner.invoke(cli, ["--help"])
    gh_result = runner.invoke(cli, ["gh", "--help"])

    assert help_result.exit_code == 0
    assert "\n  gh " not in help_result.output
    assert gh_result.exit_code != 0
    assert "No such command 'gh'" in gh_result.output


def test_chattool_aliases_do_not_shadow_chatgh():
    assert "chatgh" not in ALIAS_MAP
    assert "chattool gh" not in render_alias_block(list(ALIAS_MAP))
