import json
from pathlib import Path

from chattool.tools.opencode.session import SessionRunner, parse_action_spec


def _read_events(log_path: Path):
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_parse_action_spec_supports_payload_and_delay():
    action = parse_action_spec("send_text:0.5:hello world")
    assert action.kind == "send_text"
    assert action.delay == 0.5
    assert action.payload == "hello world"


def test_session_runner_records_io_and_actions(tmp_path):
    log_path = tmp_path / "session.jsonl"
    runner = SessionRunner(
        command=["python3", "-i", "-q"],
        log_path=log_path,
        idle_seconds=0.2,
    )

    result = runner.run(
        actions=[
            parse_action_spec("send_text:0.1:print('hi')"),
            parse_action_spec("send_enter:0.2"),
            parse_action_spec("send_eof:0.7"),
        ],
        interactive=False,
        timeout_seconds=5,
    )

    assert result.returncode == 0
    events = _read_events(log_path)
    assert any(event["kind"] == "session.start" for event in events)
    assert events[0]["mode"] == "control"
    assert any(event["kind"] == "session.output" and "hi" in event.get("text", "") for event in events)
    assert [event.get("action") for event in events if event["kind"] == "session.action"] == [
        "send_text",
        "send_enter",
        "send_eof",
    ]
    assert any(event["kind"] == "session.status" and event.get("status") == "idle" for event in events)
    assert events[-1]["kind"] == "session.end"


def test_session_runner_sigint_reaches_target_process(tmp_path):
    log_path = tmp_path / "sigint.jsonl"
    runner = SessionRunner(
        command=[
            "python3",
            "-c",
            "import signal,sys,time; signal.signal(signal.SIGINT, lambda *_: (print('got-sigint', flush=True), sys.exit(130))); time.sleep(10)",
        ],
        log_path=log_path,
        idle_seconds=0.2,
    )

    result = runner.run(
        actions=[parse_action_spec("send_sigint:0.2")],
        interactive=False,
        timeout_seconds=5,
    )

    assert result.returncode == 130
    events = _read_events(log_path)
    assert any(event["kind"] == "session.action" and event.get("action") == "send_sigint" for event in events)
    assert any(event["kind"] == "session.output" and "got-sigint" in event.get("text", "") for event in events)


def test_session_runner_supports_observe_mode(tmp_path):
    log_path = tmp_path / "observe.jsonl"
    runner = SessionRunner(
        command=["python3", "-c", "print('observe-only')"],
        log_path=log_path,
        idle_seconds=0.2,
        mirror_output=True,
    )

    result = runner.run(actions=[], interactive=False, timeout_seconds=5, mode="observe")

    assert result.returncode == 0
    events = _read_events(log_path)
    assert events[0]["mode"] == "observe"
    assert not any(event["kind"] == "session.action" for event in events)
    assert any(event["kind"] == "session.output" and "observe-only" in event.get("text", "") for event in events)
