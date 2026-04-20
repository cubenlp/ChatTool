import json

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_opencode_help_shows_commands(runner):
    result = runner.invoke(cli, ["opencode", "--help"])
    assert result.exit_code == 0
    assert "Manage OpenCode sessions through a PTY wrapper." in result.output
    assert "observe" in result.output
    assert "run" in result.output


def test_chattool_opencode_direct_wrap_mode(tmp_path, runner, monkeypatch):
    
    captured = {}

    def fake_run(self, actions=None, interactive=None, timeout_seconds=None, mode="control"):
        captured["command"] = self.command
        captured["mode"] = mode
        captured["timeout_seconds"] = timeout_seconds
        return type(
            "Result",
            (),
            {"log_path": tmp_path / "direct.jsonl", "returncode": 0},
        )()

    monkeypatch.setattr("chattool.tools.opencode.session.SessionRunner.run", fake_run)

    result = runner.invoke(cli, ["opencode", "--timeout", "3"])

    assert result.exit_code == 0
    assert captured["command"] == ["opencode"]
    assert captured["mode"] == "direct-wrap"
    assert captured["timeout_seconds"] == 3.0


def test_chattool_opencode_run_subcommand(tmp_path, runner):

    log_path = tmp_path / "session.jsonl"
    result = runner.invoke(
        cli,
        [
            "opencode",
            "run",
            "--log-path",
            str(log_path),
            "--action",
            "send_text:0.1:print('hi')",
            "--action",
            "send_enter:0.2",
            "--action",
            "send_eof:0.3",
            "--",
            "python3",
            "-i",
            "-q",
        ],
    )

    assert result.exit_code == 0
    assert f"Log: {log_path}" in result.output
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(event["kind"] == "session.output" and "hi" in event.get("text", "") for event in events)
    assert events[0]["mode"] == "control"


def test_chattool_opencode_observe_mode(tmp_path, runner):
    log_path = tmp_path / "observe.jsonl"
    result = runner.invoke(
        cli,
        [
            "opencode",
            "observe",
            "--log-path",
            str(log_path),
            "--timeout",
            "1",
            "--mirror-output",
            "--",
            "python3",
            "-c",
            "print('observe-only')",
        ],
    )

    assert result.exit_code == 0
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert events[0]["mode"] == "observe"
    assert any(event["kind"] == "session.output" and "observe-only" in event.get("text", "") for event in events)


def test_chattool_opencode_observe_wraps_explicit_command(tmp_path, runner):
    log_path = tmp_path / "observe-opencode.jsonl"
    result = runner.invoke(
        cli,
        [
            "opencode",
            "observe",
            "--log-path",
            str(log_path),
            "--timeout",
            "1",
            "--mirror-output",
            "--",
            "python3",
            "-c",
            "print('wrapped-command')",
        ],
    )

    assert result.exit_code == 0
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert events[0]["command"] == ["python3", "-c", "print('wrapped-command')"]


def test_chattool_opencode_run_requires_action(runner):
    result = runner.invoke(cli, ["opencode", "run", "--", "python3", "-c", "print('x')"])
    assert result.exit_code != 0
    assert "Control mode requires at least one --action" in result.output


def test_chattool_opencode_summarize(tmp_path, runner):
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(
        "\n".join(
            [
                json.dumps({"kind": "session.status", "status": "running"}),
                json.dumps({"kind": "session.action", "action": "send_text"}),
                json.dumps({"kind": "session.output", "text": "hello\\n"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["opencode", "summarize", str(log_path)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["event_counts"]["session.status"] == 1
    assert payload["actions"] == ["send_text"]
    assert payload["samples"] == ["session.output: hello\\n"]
