# Zulip Knowledge Base (ZulipKB)

ZulipKB 是 ChatTool 内置的一个知识库管理应用，旨在将 Zulip 中的聊天记录转化为本地可检索、可管理的知识资产。

## 核心概念

1.  **Workspace (工作区)**: 
    - 每一个工作区对应一个独立的 SQLite 数据库文件。
    - 用于隔离不同项目或上下文的知识。
2.  **Tracking (追踪)**: 
    - 你可以配置工作区只关注特定的 Zulip 频道 (Stream)。
    - 只有被追踪的频道消息才会被同步到本地。
3.  **Sync (同步)**: 
    - 增量同步机制：系统会记录每个频道最后同步的消息 ID，下次同步时只获取新消息。
4.  **Index & Search (索引与搜索)**: 
    - 本地数据库启用 Full-Text Search (FTS)，支持毫秒级全文检索。

## 快速开始

### 1. 初始化工作区

首先，创建一个名为 `work` 的工作区：

```bash
chattool kb init work
# Output: Initialized workspace 'work' at /Users/username/.chattool/kb/work.db
```

### 2. 配置追踪频道

告诉 ZulipKB 你关心哪些频道：

```bash
chattool kb track work "general"
chattool kb track work "development"
```

### 3. 同步数据

从 Zulip 服务器拉取消息（首次同步可能需要一些时间）：

```bash
chattool kb sync work
```

### 4. 浏览与阅读

查看工作区内有哪些话题：

```bash
chattool kb list work
```

输出示例：
```
Stream               | Topic                                    | Count
----------------------------------------------------------------------
general              | welcome                                  | 15   
development          | bug reports                              | 8    
```

阅读特定话题的内容：

```bash
chattool kb show work "general" "welcome"
```

### 5. 全文搜索

在本地知识库中搜索关键词（例如 "python"）：

```bash
chattool kb search work "python"
```

## 数据存储

数据默认存储在 `~/.chattool/kb/` 目录下。你可以直接使用 SQLite 客户端（如 DB Browser for SQLite）打开 `.db` 文件进行高级分析。

## 下一步计划

- [ ] **知识加工**: 添加笔记 (Note) 功能，允许对特定消息进行标注和总结。
- [ ] **导出**: 支持将话题导出为 Markdown 文档。
- [ ] **自动摘要**: 集成 LLM 对长话题进行自动摘要。
