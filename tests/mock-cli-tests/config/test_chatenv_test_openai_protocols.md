# OpenAI 双协议测试设计

## 目标
`chatenv test -t oai` / `-t openai` 默认先测 Responses，再独立测 Chat Completions；任一协议通过即说明此 profile 至少有一种可用文本接口，不把另一协议失败说成整个服务不可用。

## 初始环境准备
- 使用 ChatEnv CLI 的真实注册、profile 加载与 ChatTool provider。
- 只用测试专属 home 和 dummy profile；通过 httpx.MockTransport 隔离外网。
- 不模拟 CLI 调度；HTTP mock 仅替代服务端。测试 monkeypatch 必须自动回滚。

## 预期过程和结果
1. 默认按 `/responses`、`/chat/completions` 顺序各请求一次；前项成功或失败都不省略后项。
2. 两请求使用同一选中 profile 的 base/key/model，不走 Chat 客户端额外重试和其他配置 fallback。
3. Responses-only、Chat-only、双支持、双失败分别有明确逐项结果和总结果；双失败 CLI 非零，单支持 CLI 成功。
4. Responses streaming 的 HTTP 200 不等于生成成功：created-only、SSE error、failed、incomplete、输出后再 failed 都不得算成功。
5. Responses token budget 不再用非法的 8；留出短推理余量，缺少有效输出或预算耗尽给具体测试诊断，不宣称整个服务不支持协议。
6. Chat Completions 不用旧的 `max_tokens=5`；HTTP 200 error、空 choices、空内容、长度截断都不能误报通过。
7. 默认不打印回复正文、原始错误正文、API key 或 OAuth token；测试错误内容与生成内容包含 dummy canary 并断言输出无泄漏。
8. 缺少 base/key/model 在发请求前得到清晰诊断；请求超时有界且不自动重试。
9. Python 可调用 API 返回两协议结构化结果；CLI 只负责配置取值、展示和退出语义。
10. `chatenv --tree` / `test --help` 读取真实运行树，不添加本任务不需要的参数。

## 参考执行脚本（伪代码）
```sh
PYTHONPATH=<ChatEnv-source>:src python -m pytest -q tests/mock-cli-tests/config/test_chatenv_test_openai_protocols.py
PYTHONPATH=<ChatEnv-source>:src python -m chatenv.cli --tree
PYTHONPATH=<ChatEnv-source>:src python -m chatenv.cli test --help
# 真实现有 active profile smoke 与 mock 完全分开执行，不改 profile。
```
