import json
import os
import subprocess
import sys
from pathlib import Path


def _run_python(
    code: str, *, config_dir: Path, extra_env: dict[str, str] | None = None
):
    env = os.environ.copy()
    env["CHATTOOL_CONFIG_DIR"] = str(config_dir)
    env.pop("FEISHU_APP_ID", None)
    env.pop("FEISHU_APP_SECRET", None)
    env.pop("FEISHU_API_BASE", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_setup_lark_cli_env_ref_uses_feishu_profile_priority(tmp_path: Path):
    config_dir = tmp_path / "config"
    feishu_dir = config_dir / "envs" / "Feishu"
    feishu_dir.mkdir(parents=True, exist_ok=True)
    (feishu_dir / ".env").write_text(
        "\n".join(
            [
                "FEISHU_APP_ID='from_builtin'",
                "FEISHU_APP_SECRET='builtin_secret'",
                "FEISHU_API_BASE='https://open.feishu.cn'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (feishu_dir / "work.env").write_text(
        "\n".join(
            [
                "FEISHU_APP_ID='from_profile'",
                "FEISHU_APP_SECRET='profile_secret'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_python(
        "\n".join(
            [
                "import json",
                "from chattool.setup.lark_cli import _load_feishu_values_from_env_ref",
                "print(json.dumps(_load_feishu_values_from_env_ref('work'), ensure_ascii=False))",
            ]
        ),
        config_dir=config_dir,
        extra_env={
            "FEISHU_APP_ID": "from_os",
            "FEISHU_APP_SECRET": "os_secret",
            "FEISHU_API_BASE": "https://open.larksuite.com",
        },
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip())
    assert payload["app_id"] == "from_profile"
    assert payload["app_secret"] == "profile_secret"
    assert payload["api_base"] == "https://open.feishu.cn"


def test_setup_lark_cli_saved_feishu_values_prefer_env_file_over_os_env(tmp_path: Path):
    config_dir = tmp_path / "config"
    feishu_dir = config_dir / "envs" / "Feishu"
    feishu_dir.mkdir(parents=True, exist_ok=True)
    (feishu_dir / ".env").write_text(
        "\n".join(
            [
                "FEISHU_APP_ID='saved_app'",
                "FEISHU_APP_SECRET='saved_secret'",
                "FEISHU_API_BASE='https://open.feishu.cn'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_python(
        "\n".join(
            [
                "import json",
                "from chattool.setup.lark_cli import _load_saved_feishu_values",
                "print(json.dumps(_load_saved_feishu_values(), ensure_ascii=False))",
            ]
        ),
        config_dir=config_dir,
        extra_env={
            "FEISHU_APP_ID": "from_os",
            "FEISHU_APP_SECRET": "os_secret",
            "FEISHU_API_BASE": "https://open.larksuite.com",
        },
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip())
    assert payload["app_id"] == "saved_app"
    assert payload["app_secret"] == "saved_secret"
    assert payload["api_base"] == "https://open.feishu.cn"
