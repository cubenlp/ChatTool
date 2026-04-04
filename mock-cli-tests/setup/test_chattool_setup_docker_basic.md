# chattool setup docker basic

## Case 1: `setup docker -I` should only print suggested commands when `--sudo` is not set

### 初始环境准备

- 使用 mock 拦截命令检测与实际系统调用，避免真的执行 `sudo apt install` 或 `usermod`。

### 预期过程和结果

- 执行 `chattool setup docker -I`。
- 当检测到未安装 Docker / Docker Compose、当前用户不在 `docker` 组时，不应自动执行 sudo 命令。
- 输出中应打印对应的建议命令，并包含完成提示。

### 参考执行脚本（伪代码）

```sh
mock docker and docker-compose as missing
mock groups output without docker
run chattool setup docker -I
assert no sudo command was executed
assert output contains suggested install commands
assert output contains completion message
```

## Case 2: `setup docker --sudo -i` should only execute a sudo command after explicit confirmation

### 初始环境准备

- 使用 mock 拦截命令检测与实际系统调用，避免真的执行 `sudo`。
- 在交互测试环境下显式传入 `--sudo`。

### 预期过程和结果

- 执行 `chattool setup docker --sudo -i`。
- 当检测到 Docker 缺失时，应先询问是否立即执行建议命令。
- 只有用户明确确认后，才应执行对应的 `sudo` 命令。

### 参考执行脚本（伪代码）

```sh
mock docker as missing
run chattool setup docker --sudo -i
confirm docker install
assert sudo apt install docker.io -y was executed
```
