import pytest
from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = [pytest.mark.e2e]


def test_chattool_pypi_probe_detects_existing_project_name():
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["pypi", "probe", "--name", "mychat", "--repository", "pypi"],
    )

    assert result.exit_code == 0
    assert "[WARN] repository.project: mychat already exists on pypi" in result.output
