# test_chattool_lark_doc_permissions

测试 `chattool lark doc` 的权限管理命令，覆盖公开分享权限读取/更新，以及显式协作者读取/添加。

## 元信息

- 命令：`chattool lark doc perm-public-get|perm-public-set|perm-member-list|perm-member-add`
- 目的：验证飞书文档权限管理现在可以完全走 CLI，不再依赖临时 SDK 脚本。
- 标签：`cli`
- 前置条件：具备飞书凭证、`docx/drive` 权限，以及一个可用的测试成员 ID。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID` 或 `FEISHU_TEST_USER_ID`
  - 若使用测试用户，还需要 `FEISHU_TEST_USER_ID_TYPE`
- 回滚：使用测试文档，不影响现有正式文档权限。

## 用例 1：读取公开分享权限

- 初始环境准备：
  - 准备一个可访问的 `document_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc perm-public-get <document_id>`。
  2. 预期返回 `permission_public` JSON。
  3. 预期输出至少包含 `link_share_entity` 等核心字段。

参考执行脚本（伪代码）：

```sh
chattool lark doc perm-public-get doccnxxxxxxxxxxxx
```

## 用例 2：更新公开分享权限

- 初始环境准备：
  - 准备一个可写的 `document_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc perm-public-set <document_id> --share-entity same_tenant --link-share-entity tenant_editable`。
  2. 预期返回更新成功。
  3. 预期 JSON 中 `share_entity=same_tenant`、`link_share_entity=tenant_editable`。

参考执行脚本（伪代码）：

```sh
chattool lark doc perm-public-set doccnxxxxxxxxxxxx \
  --share-entity same_tenant \
  --link-share-entity tenant_editable
```

## 用例 3：添加显式协作者并读取列表

- 初始环境准备：
  - 准备一个可写的 `document_id`。
  - 准备一个可作为协作者的成员 ID。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc perm-member-add <document_id> <member_id> --member-type userid --perm edit`。
  2. 预期返回添加成功。
  3. 执行 `chattool lark doc perm-member-list <document_id>`。
  4. 预期列表中出现对应 `member_id`，权限为 `edit` 或更高。

参考执行脚本（伪代码）：

```sh
chattool lark doc perm-member-add doccnxxxxxxxxxxxx f25gc16d --member-type userid --perm edit
chattool lark doc perm-member-list doccnxxxxxxxxxxxx
```
