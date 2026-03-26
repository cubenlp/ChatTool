from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_listen_task(lark_testkit):
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    process = subprocess.Popen(
        [sys.executable, "-m", "chattool.client.main", "lark", "listen", "-l", "DEBUG"],
        cwd=str(lark_testkit.repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        time.sleep(3)
        assert process.poll() is None, "listen exited unexpectedly"
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        output, _ = process.communicate(timeout=10)

    assert "启动 WebSocket 监听" in output

