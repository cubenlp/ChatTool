from __future__ import annotations

import json
import re
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from dotenv import dotenv_values

from chattool.client.main import cli
from chattool.config import BaseEnvConfig, FeishuConfig
from chattool.const import CHATTOOL_ENV_DIR, CHATTOOL_ENV_FILE, CHATTOOL_REPO_DIR
from chattool.tools.lark import LarkBot


def _reload_chattool_env() -> None:
    env_values = {}
    if CHATTOOL_ENV_FILE.exists():
        env_values = dotenv_values(str(CHATTOOL_ENV_FILE))
    for config_cls in BaseEnvConfig._registry:
        config_cls.load_from_dict(env_values)


def _extract_json_from_output(output: str) -> dict:
    start = output.find("{")
    end = output.rfind("}")
    if start < 0 or end < 0 or end <= start:
        raise AssertionError(f"JSON payload not found in output:\n{output}")
    return json.loads(output[start : end + 1])


def _find_value(payload, key: str):
    if isinstance(payload, dict):
        if key in payload:
            return payload[key]
        for value in payload.values():
            found = _find_value(value, key)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_value(item, key)
            if found is not None:
                return found
    return None


def _extract_match(output: str, pattern: str, label: str) -> str:
    match = re.search(pattern, output)
    if not match:
        raise AssertionError(f"{label} not found in output:\n{output}")
    return match.group(1)


@pytest.fixture
def lark_testkit(tmp_path: Path):
    _reload_chattool_env()

    if not FeishuConfig.FEISHU_APP_ID.value or not FeishuConfig.FEISHU_APP_SECRET.value:
        pytest.skip("Feishu config is not available")

    default_receiver_id = FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value or None
    test_user_id = FeishuConfig.FEISHU_TEST_USER_ID.value or None
    test_user_id_type = FeishuConfig.FEISHU_TEST_USER_ID_TYPE.value or "user_id"
    message_receiver_id = default_receiver_id or test_user_id
    message_receiver_type = "user_id" if default_receiver_id else test_user_id_type

    def invoke(*args: str):
        runner = CliRunner()
        result = runner.invoke(cli, list(args))
        assert result.exit_code == 0, result.output
        return result

    def invoke_raw(*args: str):
        runner = CliRunner()
        return runner.invoke(cli, list(args))

    def create_document(prefix: str = "cli-doc", *, title: str | None = None):
        document_title = title or f"{prefix}-{time.time_ns()}"
        create = invoke("lark", "doc", "create", document_title)
        return SimpleNamespace(
            title=document_title,
            document_id=_extract_match(
                create.output,
                r"document_id[:=]\s*([A-Za-z0-9_]+)",
                "document_id",
            ),
            output=create.output,
        )

    def wait_doc_raw_contains(document_id: str, text: str, *, attempts: int = 5, delay: float = 1.0):
        last_output = ""
        for _ in range(attempts):
            raw = invoke("lark", "doc", "raw", document_id)
            last_output = raw.output
            if text in last_output:
                return raw
            time.sleep(delay)
        raise AssertionError(f"{text!r} not found in document raw output:\n{last_output}")

    return SimpleNamespace(
        tmp_path=tmp_path,
        repo_root=CHATTOOL_REPO_DIR,
        env_dir=CHATTOOL_ENV_DIR,
        env_file=CHATTOOL_ENV_FILE,
        bot=LarkBot(),
        invoke=invoke,
        invoke_raw=invoke_raw,
        create_document=create_document,
        wait_doc_raw_contains=wait_doc_raw_contains,
        parse_json=_extract_json_from_output,
        find_value=_find_value,
        unique_name=lambda prefix: f"{prefix}-{time.time_ns()}",
        message_receiver_id=message_receiver_id,
        message_receiver_type=message_receiver_type,
        default_receiver_id=default_receiver_id,
        test_user_id=test_user_id,
        test_user_id_type=test_user_id_type,
        message_id_from_output=lambda output: _extract_match(
            output,
            r"message_id=([A-Za-z0-9_]+)",
            "message_id",
        ),
        document_id_from_output=lambda output: _extract_match(
            output,
            r"document_id[:=]\s*([A-Za-z0-9_]+)",
            "document_id",
        ),
    )


@pytest.fixture
def lark_docaudit():
    def read(rel_path: str) -> str:
        return (CHATTOOL_REPO_DIR / rel_path).read_text(encoding="utf-8")

    def exists(rel_path: str) -> bool:
        return (CHATTOOL_REPO_DIR / rel_path).exists()

    def invoke_help(*args: str):
        runner = CliRunner()
        result = runner.invoke(cli, [*args, "--help"])
        assert result.exit_code == 0, result.output
        return result.output

    return SimpleNamespace(
        repo_root=CHATTOOL_REPO_DIR,
        env_dir=CHATTOOL_ENV_DIR,
        env_file=CHATTOOL_ENV_FILE,
        read=read,
        exists=exists,
        invoke_help=invoke_help,
    )
