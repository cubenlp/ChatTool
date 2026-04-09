from pathlib import Path


def test_chattool_release_tag_format():
    repo_root = Path(__file__).resolve().parents[3]

    release_en = (repo_root / "skills/chattool-release/SKILL.md").read_text(
        encoding="utf-8"
    )
    release_zh = (repo_root / "skills/chattool-release/SKILL.zh.md").read_text(
        encoding="utf-8"
    )
    publish_workflow = (repo_root / ".github/workflows/publish.yml").read_text(
        encoding="utf-8"
    )

    assert "`vX.Y.Z`" in release_en
    assert "`vX.Y.Z`" in release_zh
    assert "before the PR is merged" in release_en
    assert "PR 合并前" in release_zh
    assert "- 'v*'" in publish_workflow
    assert 'tag_name="${GITHUB_REF_NAME#v}"' in publish_workflow
    assert "package_version=\"$(python3 - <<'PY'" in publish_workflow
    assert "print(ast.literal_eval(stmt.value))" in publish_workflow
    assert 'if [[ "$tag_name" != "$package_version" ]]; then' in publish_workflow
    assert "Fail if version already exists on PyPI" in publish_workflow
    assert "already on PyPI" in publish_workflow
    assert "--skip-existing" not in publish_workflow
