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
from chattool.const import CHATTOOL_ENV_FILE
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


@pytest.fixture
def lark_testkit(tmp_path: Path):
    _reload_chattool_env()

    if not FeishuConfig.FEISHU_APP_ID.value or not FeishuConfig.FEISHU_APP_SECRET.value:
        pytest.skip("Feishu config is not available")

    message_receiver_id = (
        FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value
        or FeishuConfig.FEISHU_TEST_USER_ID.value
    )
    message_receiver_type = FeishuConfig.FEISHU_TEST_USER_ID_TYPE.value or "user_id"

    def invoke(*args: str):
        runner = CliRunner()
        result = runner.invoke(cli, list(args))
        assert result.exit_code == 0, result.output
        return result

    return SimpleNamespace(
        tmp_path=tmp_path,
        bot=LarkBot(),
        invoke=invoke,
        parse_json=_extract_json_from_output,
        find_value=_find_value,
        unique_name=lambda prefix: f"{prefix}-{int(time.time())}",
        message_receiver_id=message_receiver_id,
        message_receiver_type=message_receiver_type,
        test_user_id=FeishuConfig.FEISHU_TEST_USER_ID.value or None,
        test_user_id_type=FeishuConfig.FEISHU_TEST_USER_ID_TYPE.value or "user_id",
        message_id_from_output=lambda output: re.search(r"message_id=([A-Za-z0-9_]+)", output).group(1),
    )
