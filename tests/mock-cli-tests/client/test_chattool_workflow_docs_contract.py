from pathlib import Path

import pytest


pytestmark = pytest.mark.mock_cli

ROOT = Path(__file__).resolve().parents[3]


def test_publish_workflow_uses_oidc_and_master_ancestor_guard():
    workflow = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")

    assert 'tags:\n      - "v*"' in workflow
    assert "id-token: write" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "git fetch --no-tags origin master:refs/remotes/origin/master" in workflow
    assert "git merge-base --is-ancestor" in workflow
    assert "python -m twine check dist/*" in workflow
    assert ("git fetch origin master " + "--tags") not in workflow
    assert ("PYPI" + "_PASSWORD") not in workflow
    assert ("PYPI" + "_USERNAME") not in workflow
    assert ("TWINE" + "_PASSWORD") not in workflow


def test_preview_workflow_uses_site_url_and_gh_pages_fetch():
    workflow = (ROOT / ".github" / "workflows" / "preview.yaml").read_text(encoding="utf-8")

    assert "git fetch origin gh-pages --depth=1 || true" in workflow
    assert "mike deploy dev --push --update-aliases --allow-empty" in workflow
    assert "Path(\"mkdocs.yml\")" in workflow
    assert "CHATTOOL_PREVIEW_URL" in workflow
    assert "https://chattool.wzhecnu.cn/dev/" not in workflow


def test_mkdocs_material_emoji_renderer_is_configured():
    mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "site_url: https://chattool.wzhecnu.cn" in mkdocs
    assert "pymdownx.emoji:" in mkdocs
    assert "material.extensions.emoji.twemoji" in mkdocs
    assert "material.extensions.emoji.to_svg" in mkdocs


def test_pyproject_exposes_public_documentation_url():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'Homepage = "https://github.com/CubeNLP/ChatTool"' in pyproject
    assert 'Repository = "https://github.com/CubeNLP/ChatTool"' in pyproject
    assert 'Documentation = "https://chattool.wzhecnu.cn"' in pyproject
