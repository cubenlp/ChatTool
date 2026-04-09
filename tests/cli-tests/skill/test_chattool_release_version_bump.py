from pathlib import Path


def test_chattool_release_version_bump():
    repo_root = Path(__file__).resolve().parents[3]

    release_en = (repo_root / "skills/chattool-release/SKILL.md").read_text(
        encoding="utf-8"
    )
    release_zh = (repo_root / "skills/chattool-release/SKILL.zh.md").read_text(
        encoding="utf-8"
    )
    practice_en = (repo_root / "skills/practice-make-perfact/SKILL.md").read_text(
        encoding="utf-8"
    )
    practice_zh = (repo_root / "skills/practice-make-perfact/SKILL.zh.md").read_text(
        encoding="utf-8"
    )
    dev_en = (repo_root / "skills/chattool-dev-review/SKILL.md").read_text(
        encoding="utf-8"
    )
    dev_zh = (repo_root / "skills/chattool-dev-review/SKILL.zh.md").read_text(
        encoding="utf-8"
    )
    dev_index = (repo_root / "docs/development-guide/index.md").read_text(
        encoding="utf-8"
    )
    task_iter = (
        repo_root / "docs/development-guide/task-driven-iteration.md"
    ).read_text(encoding="utf-8")
    publish_workflow = (repo_root / ".github/workflows/publish.yml").read_text(
        encoding="utf-8"
    )

    assert "before the PR is merged" in release_en
    assert "Pushing the same-version tag again only reruns automation" in release_en
    assert "PR 合并前" in release_zh
    assert "再次推送同版本 tag" in release_zh

    assert "before PR/MR, not after merge" in practice_en
    assert "new PR with a new version" in practice_en
    assert "PR/MR 阶段前" in practice_zh
    assert "先把版本号 bump 到下一个版本" in practice_zh

    assert "should already be in the diff before merge" in dev_en
    assert "必须在合并前就已经出现在 diff 里" in dev_zh

    assert "若 PyPI 已存在该版本" in dev_index
    assert "开发分支在 PR/MR 前就要更新 `src/chattool/__init__.py`" in task_iter
    assert "禁止继续推同版本 tag" in task_iter

    assert "Fail if version already exists on PyPI" in publish_workflow
    assert "--skip-existing" not in publish_workflow
