# test_chattool_env_typed_profiles

测试按类型拆分后的 env 目录模型，覆盖 profile 保存/切换，以及显式 `-e` 配置对运行时优先级的影响。

## 元信息

- 命令：`chattool env ...`、`chattool lark ...`
- 目的：验证 `envs/<Config>/.env` 与 `envs/<Config>/<profile>.env` 的真实行为，以及 `显式参数 > -e/显式 env > environment > 内置 .env > default` 的加载顺序。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录作为 `CHATTOOL_CONFIG_DIR`，在真实文件系统中构造 `envs/<Config>/`。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：按类型保存与切换 profile

- 初始环境准备：
  - 创建临时配置目录。
  - 通过 `chattool env set` 写入 OpenAI 配置。
- 相关文件：
  - `<tmp>/config/envs/OpenAI/.env`
  - `<tmp>/config/envs/OpenAI/work.env`

预期过程和结果：
  1. 执行 `chattool env save work -t openai`，预期生成 `envs/OpenAI/work.env`。
  2. 修改当前 `envs/OpenAI/.env` 后执行 `chattool env use work -t openai`，预期活动配置恢复为保存内容。

参考执行脚本（伪代码）：

```sh
chattool env set OPENAI_API_KEY=sk-one
chattool env save work -t openai
chattool env set OPENAI_API_KEY=sk-two
chattool env use work -t openai
```

## 用例 2：系统环境变量覆盖类型内置 `.env`

- 初始环境准备：
  - 在 `envs/OpenAI/.env` 写入 `OPENAI_API_KEY=from_env_file`。
  - 额外设置进程环境变量 `OPENAI_API_KEY=from_os`。

预期过程和结果：
  1. 执行 `chattool env cat -t openai --no-mask`，预期读取到 `from_os`，而不是类型目录里的 `.env`。

参考执行脚本（伪代码）：

```sh
OPENAI_API_KEY=from_os chattool env cat -t openai --no-mask
```

## 用例 3：`chattool lark -e` 覆盖系统环境变量

- 初始环境准备：
  - 在 `envs/Feishu/.env` 写入一组默认飞书配置。
  - 另存一份 `envs/Feishu/work.env` 作为显式 profile。
  - 进程环境变量里写入另一组冲突值。

预期过程和结果：
  1. 以 `-e work` 进入飞书运行时加载流程，预期显式 profile 中的值优先于系统环境变量。
  2. 未传 `-e` 时，预期系统环境变量仍优先于 `envs/Feishu/.env`。

参考执行脚本（伪代码）：

```sh
FEISHU_APP_ID=from_os python -c 'from chattool.tools.lark.cli import _load_runtime_env; from chattool.config import FeishuConfig; _load_runtime_env("work"); print(FeishuConfig.FEISHU_APP_ID.value)'
python -c 'from chattool.config import FeishuConfig; print(FeishuConfig.FEISHU_APP_ID.value)'
```
