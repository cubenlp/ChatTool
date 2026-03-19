# GitHub Explore 模块设计文档

## 目标

封装 GitHub REST API v3，支持仓库搜索、元数据获取、trending 模拟等探索场景。
复用项目已有的 `GitHubClient`（`tools/github`），在此基础上做探索层封装。

---

## API 概览

| 接口 | 端点 | 认证要求 |
|------|------|---------|
| REST API v3 | `https://api.github.com/` | 可选（强烈建议） |
| GraphQL API v4 | `https://api.github.com/graphql` | 必须 |

探索模块只用 REST API v3，无需 GraphQL。

---

## 速率限制

| 场景 | 限制 |
|------|------|
| 未认证（按 IP） | 60 请求/小时 |
| 已认证（PAT） | 5,000 请求/小时 |
| 搜索（未认证） | 10 请求/分钟 |
| 搜索（已认证） | 30 请求/分钟 |

响应头：`X-RateLimit-Remaining` / `X-RateLimit-Reset`

---

## 主要端点

### 搜索

```
GET /search/repositories?q=language:python&sort=stars&order=desc&per_page=30
GET /search/code?q=filename:Dockerfile+user:torvalds
GET /search/users?q=location:beijing+followers:>1000
```

### 仓库

```
GET /repos/{owner}/{repo}                    # 元数据
GET /repos/{owner}/{repo}/readme             # README（base64）
GET /repos/{owner}/{repo}/releases           # Releases
GET /repos/{owner}/{repo}/issues             # Issues
GET /repos/{owner}/{repo}/topics             # Topics
GET /repos/{owner}/{repo}/contributors       # 贡献者
```

### Trending（官方无此端点）

用搜索接口模拟：

```
GET /search/repositories?q=created:>2025-03-12&sort=stars&order=desc
```

---

## 依赖选型

项目已依赖 `PyGithub`，直接复用，不引入新依赖。

---

## 模块设计

```
explore/github/
├── __init__.py
├── DESIGN.md          # 本文档
├── models.py          # Repo / Issue dataclass
├── client.py          # GithubExplorer：搜索、仓库信息、trending
```

### `models.py`

```python
@dataclass
class Repo:
    full_name: str       # "owner/repo"
    description: str
    url: str
    stars: int
    forks: int
    language: str
    topics: list[str]
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime

@dataclass
class Issue:
    number: int
    title: str
    state: str           # open / closed
    url: str
    created_at: datetime
    labels: list[str]
```

### `client.py` — GithubExplorer

```python
class GithubExplorer:
    def search_repos(query, sort, max_results) -> list[Repo]
    def get_repo(full_name) -> Repo
    def get_readme(full_name) -> str          # 解码后的 markdown 文本
    def get_releases(full_name, n) -> list[dict]
    def get_issues(full_name, state, n) -> list[Issue]
    def trending(language, since_days, n) -> list[Repo]   # 模拟 trending
```

---

## 注意事项

- 搜索接口有独立的速率限制，探索时注意控制频率
- `trending` 是模拟实现，按近期创建 + star 数排序，非官方 trending
- token 通过环境变量 `GITHUB_ACCESS_TOKEN` 读取，与现有 `GitHubClient` 一致
