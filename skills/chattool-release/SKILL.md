---
name: chattool-release
description: Handle ChatTool release readiness and post-merge release execution. Use when the task includes version bumps, changelog finalization, tag timing, Publish Package workflow checks, PyPI verification, or appending release.log after a real release.
version: 0.1.3
---

# ChatTool Release

Use this skill when ChatTool work includes release preparation or an actual release cut.

Boundary: this skill starts where `$chattool-dev-review` stops. Use it for merged-mainline release work, not for ordinary feature review.

## When To Use

- The user asks to cut a ChatTool release.
- The task includes `__version__`, `CHANGELOG.md`, release tags, or `Publish Package`.
- You need to confirm whether a release should happen now or only after MR/PR merge.
- You need to verify PyPI state or append `release.log` after a real release.

## Release Rules

1. Tag only from merged mainline
   - Do not tag from an unmerged PR head.
   - Fast-forward local `master` from `origin/master` before tagging.
   - Use the canonical release tag format `vX.Y.Z`, not a bare `X.Y.Z`.
   - The target version must already be bumped in `src/chattool/__init__.py` and reflected in `CHANGELOG.md` before the PR is merged. Post-merge release work should not be the first time the version changes.
   - If the PR is not merged yet, stop and report that release timing is premature.

2. Confirm release inputs first
   - Check `src/chattool/__init__.py` version.
   - Check the matching `CHANGELOG.md` entry.
   - Check whether the `vX.Y.Z` tag already exists locally or on remote.
   - Check whether PyPI already has that version if the task is a real publish.
   - If PyPI already has that version, stop. Pushing the same-version tag again only reruns automation; it does not create a new Python package release.

3. Validate the release path before pushing a tag
   - Run the smallest relevant test set.
   - Build distributions and run `twine check`.
   - Prefer validating on the minimum supported Python when the release changes compatibility claims.

4. Push the tag, then verify publish
   - Create an annotated `vX.Y.Z` tag from merged `master`.
   - Push the tag only after validation passes.
   - Check the `Publish Package` workflow, which should strip the leading `v` before comparing against `__version__` and fail loudly if PyPI already has that version, then verify the new version on PyPI.

5. Append `release.log` only after the release actually happened
   - Record time, version, tag, commit, operator, and a short summary.
   - Do not pre-write `release.log` before tag/publish success.

## Workflow

1. Confirm whether this is release prep or an actual release.
2. If actual release:
   - sync `master`
   - verify version/changelog/tag uniqueness
   - verify the target version was already merged before tagging
   - run validation
   - create and push the tag
   - verify workflow and PyPI result
   - append `release.log`
3. If prep only:
   - stop before tag creation
   - report the exact remaining merge/release steps

## Useful Commands

```bash
git fetch origin
git checkout master
git pull --ff-only origin master
git tag --list 'v*'
git ls-remote --tags origin 'v*'
python -m build
python -m twine check dist/*
chattool gh pr view --repo cubenlp/ChatTool --number <pr>
chattool gh pr checks --repo cubenlp/ChatTool --number <pr> --wait
chattool gh run view --repo cubenlp/ChatTool --run-id <id>
python - <<'PY'
import json, urllib.request
print(json.load(urllib.request.urlopen('https://pypi.org/pypi/chattool/json'))['info']['version'])
PY
```

## Output Rules

- Be explicit about whether the repository is only release-ready or already released.
- Use concrete commit hashes, tag names, workflow ids, and versions.
- Before merge or tag creation, prefer `chattool gh pr checks --wait` so CI reaches a terminal state before release decisions.
- Say explicitly when a tag would only retrigger workflow without producing a new PyPI package.
- If release timing is wrong, say so before doing anything destructive.
