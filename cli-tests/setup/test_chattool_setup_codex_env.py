import json
import os
import subprocess
import sys
from pathlib import Path


def _run_python(code: str, *, config_dir: Path, extra_env: dict[str, str] | None = None):
    env = os.environ.copy()
    env["CHATTOOL_CONFIG_DIR"] = str(config_dir)
    env.pop("OPENAI_API_KEY", None)
    env.pop("OPENAI_API_BASE", None)
    env.pop("OPENAI_API_MODEL", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_setup_codex_env_ref_uses_openai_profile_priority(tmp_path: Path):
    config_dir = tmp_path / "config"
    openai_dir = config_dir / "envs" / "OpenAI"
    openai_dir.mkdir(parents=True, exist_ok=True)
    (openai_dir / ".env").write_text(
        "\n".join(
            [
                "OPENAI_API_KEY='from_builtin'",
                "OPENAI_API_BASE='https://builtin.example/v1'",
                "OPENAI_API_MODEL='builtin-model'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (openai_dir / "work.env").write_text(
        "\n".join(
            [
                "OPENAI_API_KEY='from_profile'",
                "OPENAI_API_MODEL='profile-model'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_python(
        "\n".join(
            [
                "import json",
                "from chattool.setup.codex import _load_openai_values_from_env_ref, _snapshot_openai_values",
                "payload = {",
                "    'env_ref': _load_openai_values_from_env_ref('work'),",
                "    'current': _snapshot_openai_values(),",
                "}",
                "print(json.dumps(payload, ensure_ascii=False))",
            ]
        ),
        config_dir=config_dir,
        extra_env={
            "OPENAI_API_KEY": "from_os",
            "OPENAI_API_BASE": "https://os.example/v1",
            "OPENAI_API_MODEL": "os-model",
        },
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip())
    assert payload["env_ref"]["openai_api_key"] == "from_profile"
    assert payload["env_ref"]["base_url"] == "https://os.example/v1"
    assert payload["env_ref"]["model"] == "profile-model"
    assert payload["current"]["openai_api_key"] == "from_os"
    assert payload["current"]["base_url"] == "https://os.example/v1"
    assert payload["current"]["model"] == "os-model"
