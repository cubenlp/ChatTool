# ChatTool Skills 使用说明

`skills/` 目录用于存放可被 ChatTool 识别的技能清单（Skill Manifest）。

## 目录结构

每个技能一个子目录，建议包含：

- `SKILL.md`：英文清单
- `SKILL.zh.md`：中文清单（可选）
- `scripts/`：该技能依赖的脚本（可选）

示例：

```text
skills/
  dns/
    SKILL.md
    SKILL.zh.md
  frp-configurator/
    SKILL.md
    SKILL.zh.md
    scripts/
      setup_server.sh
```

## 当前已内置技能

- `cert-manager`
- `dns`
- `frp-configurator`
- `image`
- `network-scanner`

## 如何查看技能

通过 MCP CLI 查看：

```bash
# 列表
chattool mcp skills list --lang zh

# 查看单个技能
chattool mcp skills show dns --lang en
```

## 语言优先级

- `--lang zh`：优先读取 `SKILL.zh.md`，缺失时回退 `SKILL.md`
- `--lang en`：优先读取 `SKILL.md`，缺失时回退 `SKILL.zh.md`

## 新增技能规范

1. 在 `skills/` 下创建新目录（目录名建议用 kebab-case）。
2. 至少提供一个 Manifest（`SKILL.md` 或 `SKILL.zh.md`）。
3. Manifest 建议包含 front matter：

```yaml
---
name: "your-skill-name"
description: "一句话说明技能用途"
---
```

4. 若技能依赖脚本，放入 `scripts/` 并在 Manifest 中说明调用方式与参数约束。
