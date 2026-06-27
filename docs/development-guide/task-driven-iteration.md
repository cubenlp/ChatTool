# 任务驱动的技能与工具沉淀

本文档记录在执行任务过程中如何持续沉淀工具与技能，并保证项目结构一致。

## 基本流程

1. **先完成任务，再规范化**  
    先完成实际需求，再做文档、命名与结构整理。
   - 前期探索和方案形成阶段保持轻约束，不要让流程本身打断必要的代码阅读与尝试。
   - 当实现方向明确后，再切换到严格的规范化与提交流程。

2. **优先 CLI 交互**  
    能用 `chattool` CLI 完成的读取与导出，尽量使用 CLI，确保可复现与可审计。

   - 探索期产生的临时脚本、草稿、导出结果，优先放到仓库外的独立工作目录，例如 `~/tmp/chattool/<task>/`。
   - 不要把 scratch、试验产物或一次性导出结果默认放进当前仓库，避免污染 git 历史和项目结构。

3. **CLI 测试文档先行**  
    CLI 测试必须先写对应测试线下的 `.md`，再实现对应 `.py`，确保步骤与预期可审阅。
   - ChatTool 仓库长期维护两条 CLI 测试线：`cli-tests/` 负责真实链路，`mock-cli-tests/` 负责 mock 链路。
   - 仓库根下 `tests/` 仅作历史参考，不再作为新开发默认测试落点。
   - 需要验证真实表现时，优先构造真实文件系统、真实仓库状态和真实配置，并写入 `cli-tests/`。
   - 使用 `mock`、`patch`、`monkeypatch`、fake client / API 的 CLI 测试，统一写入 `mock-cli-tests/`。

4. **能力归类**  
   - 通用、可复用：补充到 `src/`（工具层、CLI、MCP）。  
   - 任务特定或 agent workflow 知识：维护在 workspace/ChatMemory 的共享 skills 中，不再写入 ChatTool 仓库根 `skills/`。

5. **技能落地要求**
   - ChatTool 仓库不再携带随包 `skills/` 目录；不要把历史 `skills/<name>/` 当作当前工作流事实源。
   - 需要沉淀 skill 时，先进入当前 workspace 的 `skills/` / ChatMemory 共享技能流程，并保持 source repo 与 workspace skill 的职责分离。
   - 若任务需要阶段化产物，目录层级保持简洁，优先使用仓库外目录下的 `<频道>/<主题>/` 或 `<任务>/<阶段>/`。

6. **任务后复盘**  
   - 做一次代码 review，统一命名、结构与文档。  
   - 开发规范、发版规范和包拆分规范使用当前 workspace / ChatMemory / Hermes skills；不要调用 ChatTool 仓库旧 `skills/` 路径。
   - 在这个后处理阶段，使用当前共享/Hermes 的 ChatTool/ChatArch 开发 review skill；不要引用仓库内旧 `skills/chattool-dev-review/` 路径。
   - 若任务继续进入合并后的版本 tag / 发布阶段，再切到当前共享/Hermes 的 release skill，不要把正式发版动作混进开发 review。
   - 若这次任务要进入正式发版，开发分支在 PR/MR 前就要更新 `src/chattool/__init__.py` 和对应 `CHANGELOG.md` 到目标版本；合并后只负责从主线打同版本的 `vX.Y.Z` tag，不要等到合并后再补改版本号。
   - 正式发版的标准 tag 统一为 `vX.Y.Z`，且只能从已合并并同步到最新的主线创建。
   - 如果 PyPI 已经存在该版本，禁止继续推同版本 tag 试图“重发”；必须先提交新的版本 bump 变更，再走下一次合并后发版。
   - 更新导航（如 `mkdocs.yml`）与文档索引。
   - 将任务推进到 PR/MR 阶段，而不是只停留在本地提交。
   - GitHub 读取与检查流程优先使用独立 `chatgh`，例如 `pr list`、`pr view`、`pr checks`、`run view`、`run logs`、`repo-perms`、`set-token`；PR 创建/编辑/合并等写操作在 ChatGH 暂未公开为稳定 CLI 前，使用项目既有工作流或 GitHub API。
   - 在声称“PR 可合并”或“CI 已通过”之前，必须先同步最新 base 分支，并验证一次真实合并态：`git fetch origin <base>` 后，查看 `chatgh pr view <number>` / `chatgh pr checks <number>` 的 `mergeable`、`mergeable_state`，必要时在最新 base 上做临时 merge/rebase 演练并在该结果上跑最相关测试。

## 结果目标

- 每次任务都有产出：工具、技能或文档。  
- 项目结构不分叉，既能完成任务，也能积累长期能力。
