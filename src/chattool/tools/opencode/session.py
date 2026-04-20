from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import fcntl
import json
import os
import pty
import select
import signal
import struct
import subprocess
import sys
import termios
import time
import tty


CTRL_D = b"\x04"
ENTER_KEY = b"\r"
DEFAULT_IDLE_SECONDS = 1.0


@dataclass(frozen=True)
class SessionAction:
    kind: str
    delay: float = 0.0
    payload: str = ""


@dataclass(frozen=True)
class SessionEvent:
    kind: str
    timestamp: float
    data: dict[str, object]


@dataclass(frozen=True)
class SessionResult:
    command: list[str]
    returncode: int
    log_path: Path
    started_at: float
    ended_at: float


def _sanitize_text(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    return text.replace("\r", "\\r").replace("\n", "\\n")


def parse_action_spec(spec: str) -> SessionAction:
    parts = spec.split(":", 2)
    if len(parts) == 1:
        return SessionAction(kind=parts[0].strip())
    if len(parts) == 2:
        return SessionAction(kind=parts[0].strip(), delay=float(parts[1] or 0.0))
    return SessionAction(
        kind=parts[0].strip(),
        delay=float(parts[1] or 0.0),
        payload=parts[2],
    )


class EventLogger:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: SessionEvent) -> None:
        payload = {
            "kind": event.kind,
            "timestamp": event.timestamp,
            **event.data,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


class SessionRunner:
    def __init__(
        self,
        command: list[str],
        log_path: Path,
        cwd: Path | None = None,
        idle_seconds: float = DEFAULT_IDLE_SECONDS,
        mirror_output: bool = False,
    ):
        if not command:
            raise ValueError("command must not be empty")
        self.command = command
        self.cwd = cwd
        self.idle_seconds = idle_seconds
        self.mirror_output = mirror_output
        self.logger = EventLogger(log_path)

    def _emit(self, kind: str, **data: object) -> None:
        self.logger.write(SessionEvent(kind=kind, timestamp=time.time(), data=data))

    def _sync_winsize(self, stdin_fd: int, master_fd: int, proc: subprocess.Popen[bytes]) -> None:
        try:
            winsize = fcntl.ioctl(stdin_fd, termios.TIOCGWINSZ, b"\0" * 8)
            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGWINCH)
            rows, cols, _, _ = struct.unpack("HHHH", winsize)
            self._emit("session.resize", rows=rows, cols=cols)
        except OSError:
            return

    def _handle_action(self, master_fd: int, proc: subprocess.Popen[bytes], action: SessionAction) -> None:
        self._emit("session.action", action=action.kind, payload=action.payload)
        if action.kind == "send_text":
            os.write(master_fd, action.payload.encode("utf-8"))
            return
        if action.kind == "send_enter":
            os.write(master_fd, ENTER_KEY)
            return
        if action.kind == "send_eof":
            os.write(master_fd, CTRL_D)
            return
        if action.kind == "send_sigint":
            os.killpg(proc.pid, signal.SIGINT)
            return
        raise ValueError(f"unsupported action kind: {action.kind}")

    def run(
        self,
        actions: list[SessionAction] | None = None,
        interactive: bool | None = None,
        timeout_seconds: float | None = None,
        mode: str = "control",
    ) -> SessionResult:
        actions = sorted(actions or [], key=lambda item: item.delay)
        started_at = time.time()
        monotonic_start = time.monotonic()
        interactive_mode = bool(
            interactive if interactive is not None else sys.stdin.isatty() and sys.stdout.isatty()
        )
        master_fd, slave_fd = pty.openpty()
        proc = subprocess.Popen(
            self.command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=str(self.cwd) if self.cwd else None,
            preexec_fn=os.setsid,
            close_fds=True,
        )
        os.close(slave_fd)
        self._emit(
            "session.start",
            command=self.command,
            pid=proc.pid,
            cwd=str(self.cwd or Path.cwd()),
            mode=mode,
        )
        self._emit("session.status", status="running")

        old_stdin_attrs = None
        stdin_fd = None
        if interactive_mode:
            stdin_fd = sys.stdin.fileno()
            old_stdin_attrs = termios.tcgetattr(stdin_fd)
            tty.setraw(stdin_fd)
            self._sync_winsize(stdin_fd, master_fd, proc)

            old_winch_handler = signal.getsignal(signal.SIGWINCH)

            def _on_winch(signum, frame):
                self._sync_winsize(stdin_fd, master_fd, proc)
                if callable(old_winch_handler):
                    old_winch_handler(signum, frame)

            signal.signal(signal.SIGWINCH, _on_winch)
        else:
            old_winch_handler = None

        next_action_index = 0
        last_activity_at = time.monotonic()
        idle_reported = False

        try:
            while True:
                if timeout_seconds is not None and time.monotonic() - monotonic_start > timeout_seconds:
                    self._emit("session.timeout", timeout_seconds=timeout_seconds)
                    os.killpg(proc.pid, signal.SIGTERM)
                    break

                while next_action_index < len(actions):
                    action = actions[next_action_index]
                    if time.monotonic() - monotonic_start < action.delay:
                        break
                    self._handle_action(master_fd, proc, action)
                    next_action_index += 1
                    last_activity_at = time.monotonic()
                    idle_reported = False

                if proc.poll() is not None:
                    break

                read_targets: list[int] = [master_fd]
                if interactive_mode and stdin_fd is not None:
                    read_targets.append(stdin_fd)

                ready, _, _ = select.select(read_targets, [], [], 0.1)

                if master_fd in ready:
                    try:
                        data = os.read(master_fd, 4096)
                    except OSError:
                        break
                    if not data:
                        break
                    self._emit("session.output", size=len(data), text=_sanitize_text(data))
                    last_activity_at = time.monotonic()
                    idle_reported = False
                    if interactive_mode or self.mirror_output:
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()

                if interactive_mode and stdin_fd is not None and stdin_fd in ready:
                    try:
                        data = os.read(stdin_fd, 4096)
                    except OSError:
                        break
                    if not data:
                        break
                    os.write(master_fd, data)
                    self._emit("session.input", size=len(data), text=_sanitize_text(data), source="user")
                    last_activity_at = time.monotonic()
                    idle_reported = False

                if not idle_reported and time.monotonic() - last_activity_at >= self.idle_seconds:
                    self._emit("session.status", status="idle")
                    idle_reported = True
        finally:
            if interactive_mode and stdin_fd is not None and old_stdin_attrs is not None:
                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_stdin_attrs)
            if old_winch_handler is not None:
                signal.signal(signal.SIGWINCH, old_winch_handler)
            try:
                os.close(master_fd)
            except OSError:
                pass
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                except OSError:
                    pass

        ended_at = time.time()
        self._emit("session.status", status="exited", returncode=proc.returncode)
        self._emit("session.end", returncode=proc.returncode, duration_seconds=ended_at - started_at)
        return SessionResult(
            command=self.command,
            returncode=proc.returncode or 0,
            log_path=self.logger.log_path,
            started_at=started_at,
            ended_at=ended_at,
        )
