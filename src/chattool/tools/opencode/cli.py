from __future__ import annotations

import json
from pathlib import Path
import time

import click

from chattool.tools.opencode.session import SessionRunner, parse_action_spec


def _default_log_path(prefix: str) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return Path.cwd() / ".chattool" / "opencode" / f"{prefix}-{stamp}.jsonl"


DEFAULT_OPENCODE_COMMAND = ["opencode"]


def _normalize_command(command) -> list[str]:
    command_parts = list(command)
    if command_parts and command_parts[0] == "--":
        command_parts = command_parts[1:]
    if not command_parts:
        raise click.ClickException(
            "Provide a wrapped command after --, for example: chattool opencode observe -- opencode"
        )
    return command_parts


def _build_runner(log_path, cwd, idle_seconds, mirror_output, command_parts):
    resolved_log_path = log_path or _default_log_path("observe")
    return (
        SessionRunner(
            command=command_parts,
            log_path=resolved_log_path,
            cwd=cwd,
            idle_seconds=idle_seconds,
            mirror_output=mirror_output,
        ),
        resolved_log_path,
    )


@click.group(
    name="opencode",
    invoke_without_command=True,
    context_settings={"ignore_unknown_options": True},
)
@click.option(
    "--log-path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="JSONL event log path for direct wrap mode.",
)
@click.option(
    "--cwd",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
    help="Working directory for the wrapped OpenCode session.",
)
@click.option("--timeout", "timeout_seconds", type=float, default=None, help="Optional session timeout in seconds for direct wrap mode.")
@click.option("--idle-seconds", type=float, default=1.0, show_default=True, help="Emit idle status after this quiet period.")
@click.option("--mirror-output/--no-mirror-output", default=False, show_default=True, help="Mirror PTY output even when stdin is not a TTY.")
@click.pass_context
def cli(ctx, log_path, cwd, timeout_seconds, idle_seconds, mirror_output):
    """Manage OpenCode sessions through a PTY wrapper."""
    if ctx.invoked_subcommand is not None:
        return

    runner, _ = _build_runner(
        log_path=log_path,
        cwd=cwd,
        idle_seconds=idle_seconds,
        mirror_output=mirror_output,
        command_parts=DEFAULT_OPENCODE_COMMAND,
    )
    result = runner.run(actions=[], timeout_seconds=timeout_seconds, mode="direct-wrap")
    click.echo(f"Log: {result.log_path}")
    click.echo(f"Return code: {result.returncode}")


@cli.command(name="run", context_settings={"ignore_unknown_options": True})
@click.option(
    "--log-path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="JSONL event log path.",
)
@click.option(
    "--cwd",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
    help="Working directory for the wrapped command.",
)
@click.option(
    "--action",
    "action_specs",
    multiple=True,
    help="Scheduled action spec: kind[:delay[:payload]]",
)
@click.option("--timeout", "timeout_seconds", type=float, default=None, help="Optional session timeout in seconds.")
@click.option("--idle-seconds", type=float, default=1.0, show_default=True, help="Emit idle status after this quiet period.")
@click.option("--mirror-output/--no-mirror-output", default=False, show_default=True, help="Mirror PTY output even when stdin is not a TTY.")
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
def run_session(log_path, cwd, action_specs, timeout_seconds, idle_seconds, mirror_output, command):
    """Run an interactive command under external PTY observation/control."""
    command_parts = _normalize_command(command)
    if not action_specs:
        raise click.ClickException(
            "Control mode requires at least one --action. Use `chattool opencode observe -- ...` for read-only observation."
        )

    resolved_log_path = log_path or _default_log_path("session")
    runner = SessionRunner(
        command=command_parts,
        log_path=resolved_log_path,
        cwd=cwd,
        idle_seconds=idle_seconds,
        mirror_output=mirror_output,
    )
    result = runner.run(
        actions=[parse_action_spec(spec) for spec in action_specs],
        timeout_seconds=timeout_seconds,
        mode="control",
    )
    click.echo(f"Log: {result.log_path}")
    click.echo(f"Return code: {result.returncode}")


@cli.command(name="observe", context_settings={"ignore_unknown_options": True})
@click.option(
    "--log-path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="JSONL event log path.",
)
@click.option(
    "--cwd",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
    help="Working directory for the wrapped command.",
)
@click.option("--timeout", "timeout_seconds", type=float, default=None, help="Optional session timeout in seconds.")
@click.option("--idle-seconds", type=float, default=1.0, show_default=True, help="Emit idle status after this quiet period.")
@click.option("--mirror-output/--no-mirror-output", default=False, show_default=True, help="Mirror PTY output even when stdin is not a TTY.")
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
def observe_session(log_path, cwd, timeout_seconds, idle_seconds, mirror_output, command):
    """Run a wrapped command in read-only observation mode."""
    command_parts = _normalize_command(command)
    runner, resolved_log_path = _build_runner(
        log_path=log_path,
        cwd=cwd,
        idle_seconds=idle_seconds,
        mirror_output=mirror_output,
        command_parts=command_parts,
    )
    result = runner.run(actions=[], timeout_seconds=timeout_seconds, mode="observe")
    click.echo(f"Log: {result.log_path}")
    click.echo(f"Return code: {result.returncode}")


@cli.command(name="summarize")
@click.argument("log_path", type=click.Path(exists=True, path_type=Path, dir_okay=False))
def summarize_log(log_path: Path):
    """Summarize PTY observation/control evidence from a JSONL event log."""
    counts: dict[str, int] = {}
    statuses: list[str] = []
    actions: list[str] = []
    samples: list[str] = []
    for raw_line in log_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        event = json.loads(raw_line)
        kind = str(event.get("kind", "unknown"))
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "session.status":
            statuses.append(str(event.get("status")))
        if kind == "session.action":
            actions.append(str(event.get("action")))
        if kind in {"session.input", "session.output"} and len(samples) < 3:
            samples.append(f"{kind}: {event.get('text', '')}")

    payload = {
        "log_path": str(log_path),
        "event_counts": counts,
        "statuses": statuses,
        "actions": actions,
        "samples": samples,
    }
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
