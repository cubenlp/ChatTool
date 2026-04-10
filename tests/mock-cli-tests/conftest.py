from pathlib import Path
import sys

from click.testing import CliRunner

import pytest

import chattool.client.main as client_main


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def restore_chattool_root_lazy_state():
    commands = dict(client_main.cli.commands)
    lazy_commands = dict(client_main.cli._lazy_commands)
    yield
    client_main.cli.commands.clear()
    client_main.cli.commands.update(commands)
    client_main.cli._lazy_commands.clear()
    client_main.cli._lazy_commands.update(lazy_commands)
