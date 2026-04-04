import pytest

from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_docker_non_interactive_only_prints_suggestions(monkeypatch):
    commands = []

    def fake_run(command, capture_output=True, text=True):
        commands.append(command)

        class Result:
            def __init__(self, returncode=0, stdout="", stderr=""):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        if command[:2] == ["groups", "tester"]:
            return Result(stdout="tester sudo")
        return Result(returncode=1)

    monkeypatch.setenv("USER", "tester")
    monkeypatch.setattr("chattool.setup.docker.shutil.which", lambda name: None)
    monkeypatch.setattr("chattool.setup.docker._run", fake_run)

    result = CliRunner().invoke(cli, ["setup", "docker", "-I"])

    assert result.exit_code == 0
    assert "Docker not found." in result.output
    assert "Suggested: sudo apt install docker.io -y" in result.output
    assert "Suggested download command:" in result.output
    assert "Suggested: sudo cp" in result.output
    assert "Suggested: sudo usermod -aG docker tester" in result.output
    assert "Docker setup check completed." in result.output
    assert not any(command and command[0] == "sudo" for command in commands)


def test_setup_docker_with_sudo_runs_only_after_confirmation(monkeypatch):
    commands = []

    def fake_run(command, capture_output=True, text=True):
        commands.append(command)

        class Result:
            def __init__(self, returncode=0, stdout="", stderr=""):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        if command[:2] == ["groups", "tester"]:
            return Result(stdout="tester sudo")
        if command[:4] == ["sudo", "apt", "install", "docker.io"]:
            return Result(returncode=0)
        return Result(returncode=1)

    answers = iter([True, False, False])

    monkeypatch.setenv("USER", "tester")
    monkeypatch.setattr("chattool.setup.docker.shutil.which", lambda name: None)
    monkeypatch.setattr("chattool.setup.docker._run", fake_run)
    monkeypatch.setattr(
        "chattool.setup.docker.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (
            interactive,
            True,
            False,
            True,
            True,
        ),
    )
    monkeypatch.setattr(
        "chattool.setup.docker.ask_confirm",
        lambda message, default=False: next(answers),
    )

    result = CliRunner().invoke(cli, ["setup", "docker", "--sudo"])

    assert result.exit_code == 0
    assert ["sudo", "apt", "install", "docker.io", "-y"] in commands
    assert "Install Docker completed." in result.output
