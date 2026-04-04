import pytest

from click.testing import CliRunner

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_docker_nas_generates_compose_and_env(tmp_path):
    output_dir = tmp_path / "docker-nas"

    result = CliRunner().invoke(cli, ["docker", "nas", str(output_dir)])

    assert result.exit_code == 0

    compose_file = output_dir / "docker-compose.yaml"
    env_file = output_dir / "nas.env.example"

    assert compose_file.exists()
    assert env_file.exists()

    compose_text = compose_file.read_text(encoding="utf-8")
    env_text = env_file.read_text(encoding="utf-8")

    assert "fileserver:" in compose_text
    assert "image: ${IMAGE}" in compose_text
    assert '- "${RESOURCE_DIR}:/web"' in compose_text
    assert '- "${BIND_IP}:${PORT}:8080"' in compose_text
    assert "URL_PREFIX: ${URL_PREFIX}" in compose_text

    assert "RESOURCE_DIR=/nas/resources" in env_text
    assert "PORT=9080" in env_text
    assert "URL_PREFIX=/cubenlp" in env_text
