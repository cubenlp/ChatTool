# test_chattool_docker_basic

测试 `chattool docker` 的基础链路，覆盖模板与输出目录的基本行为。

## 元信息

- 命令：`chattool docker [template] [output_dir] [args]`
- 目的：验证 docker 模板生成 CLI 的基础可用性。
- 标签：`cli`
- 前置条件：无
- 环境准备：准备可写输出目录。
- 回滚：删除生成的文件。

## 用例 1：帮助信息

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool docker --help`，预期输出参数说明。

参考执行脚本（伪代码）：

```sh
chattool docker --help
```

## 用例 2：生成模板文件

- 初始环境准备：
  - 准备模板名称与输出目录。
- 相关文件：
  - `<output_dir>/docker-compose.yaml`
  - `<output_dir>/<template>.env.example`

预期过程和结果：
  1. 执行 `chattool docker <template> <output_dir>`，预期生成 compose 与 env 文件。
  2. `template` 可选值为 `chromium`、`playwright`、`headless-chromedriver`。
  3. 当未提供参数且可交互时，预期进入交互式选择。

参考执行脚本（伪代码）：

```sh
chattool docker chromium /tmp/docker-demo
chattool docker -i
```

## 清理 / 回滚

- 删除输出目录。
