from click.testing import CliRunner

from chattool.client.main import cli


def test_actions_diagnostics_moved_to_chatgh():
    runner = CliRunner()

    result = runner.invoke(cli, ["gh", "run", "view", "--run-id", "23494900414"])

    assert result.exit_code != 0
    assert "No such command 'gh'" in result.output
