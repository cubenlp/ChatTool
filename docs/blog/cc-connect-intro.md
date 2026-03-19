# cc-connect：把你的本地 AI Agent 装进口袋

你是否也遇到过这样的场景：
- 下班路上，突然想到一个绝妙的代码思路，想让 AI 试着写写看，但电脑不在手边？
- 周末在外，服务器突然报警，急需 AI 帮你分析日志，却还要掏出电脑连热点？
- 躺在床上刷手机，看到一篇好的技术文章，想让 AI 总结一下，却懒得开电脑？

如果能把运行在本地电脑上的 **Claude Code**、**Cursor Agent** 装进手机里的 **飞书**、**微信** 或者 **Telegram**，是不是就很酷？

今天介绍的开源项目 **cc-connect**，就是为了解决这个问题而生的。

---

## 什么是 cc-connect？

简单来说，[cc-connect](https://github.com/chenhg5/cc-connect) 是一个**桥梁**。

它的一端连接着你本地强大的 AI Agent（如 Claude Code, Cursor, Gemini CLI 等），另一端连接着你常用的即时通讯软件（如飞书, 钉钉, 企业微信, Telegram, Discord 等）。

通过它，你可以**随时随地**，用**任何设备**，通过**自然语言**与你的本地 AI Agent 进行交互。

## 为什么要用它？

### 1. 把 AI 带在身边 🌍
打破了 AI Agent 只能在终端（Terminal）里使用的限制。无论是通勤路上、会议间隙，还是躺在沙发上，你都可以通过手机指挥你的 AI 干活。

### 2. 支持超多平台 📱
目前已经支持了市面上主流的聊天软件：
- **国内**：飞书、钉钉、企业微信、QQ（通过 NapCat）
- **国外**：Telegram, Slack, Discord, LINE

而且，大部分平台（飞书、钉钉、Telegram、Slack、Discord）都支持 **WebSocket 模式**。这意味着：**你不需要公网 IP，也不需要搞复杂的内网穿透，直接在本地电脑运行即可！**

### 3. 支持多种 Agent 🤖
不仅仅是 Claude Code，它还支持：
- **Claude Code** (Anthropic 官方 CLI)
- **Cursor Agent** (Cursor 编辑器的 Agent 模式)
- **Gemini CLI** (Google)
- **Qoder CLI**
- **OpenCode**
- **iFlow CLI**

甚至，你可以在一个 `cc-connect` 进程里同时跑多个项目，比如用飞书控制 Claude Code 写后端，用 Telegram 控制 Cursor 写前端。

### 4. 强大的多模态能力 📸 🎙️
- **发语音**：不想打字？直接发语音，它能听懂（集成 Whisper）。
- **发图片**：看到报错截图？直接发给它，让它帮你分析。
- **回传文件**：Agent 生成的代码文件、图片、PDF，它都能直接发回给你。

---

## 快速上手

只需要三步，就能把 Claude Code 装进飞书里。

### 第一步：安装

推荐使用 `npm` 安装（也可以去 GitHub Releases 下载二进制文件）：

```bash
npm install -g cc-connect
```

### 第二步：配置

创建配置文件 `~/.cc-connect/config.toml`。这里以 **飞书 (Feishu)** + **Claude Code** 为例：

```toml
# 全局日志配置
[log]
level = "info"

# 定义一个项目
[[projects]]
name = "my-awesome-project"

# 配置 Agent (这里用 Claude Code)
[projects.agent]
type = "claudecode"

[projects.agent.options]
work_dir = "/Users/me/workspace/my-project" # Agent 的工作目录
mode = "default" # 默认模式，关键操作会询问你

# 配置平台 (这里用飞书)
[[projects.platforms]]
type = "feishu"

[projects.platforms.options]
app_id = "cli_xxxxxxxx"       # 飞书开发者后台获取
app_secret = "xxxxxxxxxxxx"   # 飞书开发者后台获取
```

> **提示**：关于如何获取飞书的 App ID 和 Secret，以及如何开启机器人能力，可以参考 [飞书 CLI 使用教程](../tools/lark/index.md)。

### 第三步：启动

```bash
cc-connect
```

启动成功后，你会看到类似的日志：
```
level=INFO msg="cc-connect is running" projects=1
```

现在，打开飞书，给你的机器人发一句 "Hello"，它应该就会回复你了！

---

## 进阶玩法

### 1. 定时任务 (Cron) ⏰

你可以直接用自然语言告诉 Agent 设置定时任务。

> **你**：每天早上 9 点，帮我检查一下 GitHub Trending 的热门项目，并总结发给我。
>
> **Agent**：好的，已添加定时任务：`0 9 * * *`。

到了第二天早上 9 点，你的飞书就会准时收到 AI 发来的日报。

### 2. 权限控制 (Human-in-the-loop) 🛡️

担心 AI 乱改代码？`cc-connect` 完美继承了 Agent 的权限控制机制。

当 Claude Code 想要修改文件或执行命令时，它会向你发送请求：
> **Agent**：我需要读取 `main.go` 文件，可以吗？
>
> **你**：(点击卡片上的) **允许** / **拒绝** / **允许所有**

在手机上点一点，就能安全地把控 AI 的行为。

### 3. 多 Agent 协作 🤝

你可以把多个机器人拉到一个群里，让它们互相协作。利用 `cc-connect` 的 Relay 机制，你甚至可以让 Claude Code 写好代码，然后让另一个负责测试的 Agent 进行 Review。

---

## 总结

**cc-connect** 让本地 AI Agent 的使用场景被无限放大了。它不再是一个冷冰冰的命令行工具，而是一个随时待命、触手可及的智能助手。

无论你是想在通勤路上处理紧急 Bug，还是想利用碎片时间进行头脑风暴，cc-connect 都是你的绝佳伴侣。

🔗 **项目地址**：[https://github.com/chenhg5/cc-connect](https://github.com/chenhg5/cc-connect)

觉得好用的话，别忘了给作者点个 Star 🌟 哦！
