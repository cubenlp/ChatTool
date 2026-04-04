# test_chattool_docker_basic

测试 `chattool docker` 的模板生成编排，补充 `nas` 模板的 mock 验证。

## 用例 1：`docker nas` 应生成 compose 与 env 示例

### 初始环境准备

- 准备临时输出目录。

### 预期过程和结果

- 执行 `chattool docker nas <output_dir>`。
- 应生成 `docker-compose.yaml` 与 `nas.env.example`。
- compose 内容应包含 `fileserver` 服务、`${RESOURCE_DIR}:/web` 挂载、`${BIND_IP}:${PORT}:8080` 端口映射。
- env 示例应包含 `RESOURCE_DIR=/nas/resources`、`PORT=9080`、`URL_PREFIX=/cubenlp`。

### 参考执行脚本（伪代码）

```sh
run chattool docker nas /tmp/docker-nas
assert docker-compose.yaml contains fileserver static-file-server volume and port mapping
assert nas.env.example contains RESOURCE_DIR PORT URL_PREFIX defaults
```
