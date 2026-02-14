# Zulip Knowledge Structure

Zulip 采用独特的**基于话题 (Topic-based)** 的线程模型，这与传统的即时通讯软件（如 Slack, Discord）或邮件列表有所不同。理解这一结构对于构建高效的知识库至关重要。

## Core Concepts (核心概念)

### 1. Organization (组织/Realm)
最高层级的容器，通常对应一个公司或社区。所有的用户、频道和消息都属于一个 Organization。

### 2. Stream (频道/流)
- **定义**: 类似于其他工具中的 "Channel" 或 "Folder"。
- **用途**: 用于广泛的主题分类，如 `#general`, `#development`, `#marketing`。
- **属性**:
  - **Public (公开)**: 组织内任何人都可以加入和查看。
  - **Private (私有)**: 仅限受邀用户可见。

### 3. Topic (话题/主题)
- **定义**: Stream 下的细分单元，是 Zulip 最核心的特性。
- **用途**: 每一条消息都**必须**属于某个 Topic。这使得在同一个 Stream 中可以并行讨论多个具体事务，而不会相互干扰。
- **类比**: 就像电子邮件的主题行 (Subject line)。
- **示例**: 在 `#development` 频道下，可以同时有 `frontend bug`, `API design`, `deploy failed` 等多个 Topic。

### 4. Message (消息)
- **定义**: 通讯的基本单元。
- **类型**:
  - **Stream Message**: 发送到特定 Stream 和 Topic 的消息。这是知识库的主要来源。
  - **Private Message (PM)**: 点对点或群组私信。通常不作为公开知识库的一部分。

## Knowledge Mapping (知识映射)

在 ChatTool 的 ZulipKB 应用中，我们将上述结构映射为本地知识库：

| Zulip Concept | KB Concept | Description |
|---------------|------------|-------------|
| **Stream**    | Category   | 知识的一级分类。用户可以选择追踪 (Track) 感兴趣的 Stream。 |
| **Topic**     | Thread/Doc | 知识的最小完整单元。通常一个 Topic 下的讨论构成了一个完整的上下文。 |
| **Message**   | Content    | 知识的具体内容。 |

## Best Practices (最佳实践)

1.  **Topic is Key**: 在 Zulip 中，Topic 是知识检索的关键。良好的 Topic 命名规范（如 `Project A: Kickoff`）能极大提升知识的可发现性。
2.  **Threaded Conversation**: 鼓励用户始终在正确的 Topic 下回复，保持上下文连贯。
3.  **Resolve Topics**: 当一个问题解决或讨论结束时，可以标记 Topic 为 resolved（通过 Zulip 界面），这在知识库中可以作为归档的标志。
