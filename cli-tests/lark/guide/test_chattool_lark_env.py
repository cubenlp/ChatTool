from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_env(lark_testkit):
    env_path = lark_testkit.tmp_path / "feishu.env"
    env_path.write_text(
        "\n".join(
            [
                f"FEISHU_APP_ID={lark_testkit.bot.app_id}",
                f"FEISHU_APP_SECRET={lark_testkit.bot.app_secret}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    file_result = lark_testkit.invoke("lark", "info", "-e", str(env_path))
    assert "名称" in file_result.output
    assert "激活状态" in file_result.output

    profile_name = f"pytest-feishu-{lark_testkit.unique_name('profile')}"
    profile_path = lark_testkit.env_dir / f"{profile_name}.env"
    profile_path.write_text(env_path.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        profile_result = lark_testkit.invoke("lark", "info", "-e", profile_name)
        assert "名称" in profile_result.output
        assert "激活状态" in profile_result.output
    finally:
        if profile_path.exists():
            profile_path.unlink()

