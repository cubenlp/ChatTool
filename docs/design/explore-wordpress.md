# WordPress Explore 模块设计文档

## 目标

封装 WordPress REST API（wp-json），支持对任意 WordPress 站点的文章、分类、标签、
用户等内容的只读探索，以及认证后的内容写入。

---

## API 概览

WordPress 4.7+ 内置 REST API，无需插件，无需注册。

| 场景 | 端点前缀 |
|------|---------|
| 自建站 | `https://yoursite.com/wp-json/wp/v2/` |
| WordPress.com | `https://public-api.wordpress.com/wp/v2/sites/{site}/` |

发现端点：`GET /wp-json/` 返回站点所有可用路由。

---

## 主要端点与参数

### Posts

```
GET /wp-json/wp/v2/posts
  ?per_page=100         # 每页数量（上限 100）
  &page=2               # 页码
  &search=keyword       # 全文搜索
  &categories=3,5       # 按分类 ID 过滤
  &tags=7               # 按标签 ID 过滤
  &author=1             # 按作者 ID
  &orderby=date         # date / title / relevance / id
  &order=desc
  &_fields=id,title,link,date,excerpt   # 按需裁剪字段
```

返回关键字段：`id` `date` `slug` `title.rendered` `content.rendered`
`excerpt.rendered` `author` `categories` `tags` `link` `featured_media`

### 其他资源

```
GET /wp-json/wp/v2/pages
GET /wp-json/wp/v2/categories?per_page=100&hide_empty=true
GET /wp-json/wp/v2/tags?search=python
GET /wp-json/wp/v2/users          # 只返回有公开文章的作者
GET /wp-json/wp/v2/media?media_type=image
GET /wp-json/wp/v2/comments?post=123
```

---

## 分页机制

通过响应头读取总量：

```
X-WP-Total: 243
X-WP-TotalPages: 25
```

---

## 认证

| 方式 | 适用场景 |
|------|---------|
| 无认证 | 只读公开内容（探索场景默认） |
| Application Passwords | 自建站写操作，WP 5.6+ 内置，推荐 |
| JWT（插件） | 前后端分离场景 |

```python
# Application Passwords
from requests.auth import HTTPBasicAuth
auth = HTTPBasicAuth("username", "xxxx xxxx xxxx xxxx xxxx xxxx")
```

未认证可读：公开 posts、pages、categories、tags、media、有文章的 users
认证后额外：草稿/私有内容、创建/更新/删除、所有 users

---

## 依赖选型

直接用 `requests`，REST API 结构简单，无需额外封装库。

---

## 模块设计

```
explore/wordpress/
├── __init__.py
├── DESIGN.md          # 本文档
├── models.py          # Post / Category / Tag dataclass
├── client.py          # WordPressClient：读取文章、分类、标签等
```

### `models.py`

```python
@dataclass
class Post:
    id: int
    slug: str
    title: str           # title.rendered 解码后
    content: str         # content.rendered
    excerpt: str
    date: datetime
    link: str
    author_id: int
    categories: list[int]
    tags: list[int]

@dataclass
class Term:              # 通用：Category / Tag
    id: int
    name: str
    slug: str
    count: int
    description: str
    link: str
```

### `client.py` — WordPressClient

```python
class WordPressClient:
    def __init__(site_url, auth=None)

    # 只读
    def get_posts(search, categories, tags, page, per_page) -> list[Post]
    def iter_posts(search, categories, tags) -> Iterator[Post]   # 自动翻页
    def get_post(post_id) -> Post
    def get_categories(hide_empty) -> list[Term]
    def get_tags(search) -> list[Term]
    def get_pages(per_page) -> list[Post]

    # 写操作（需认证）
    def create_post(title, content, status, categories, tags) -> Post
    def update_post(post_id, **fields) -> Post
```

---

## 注意事项

- 不同站点可能禁用 REST API 或限制匿名访问，需做好错误处理
- `content.rendered` 是 HTML，探索时可用 `html.parser` 提取纯文本
- WordPress.com 站点需走 OAuth2，与自建站认证方式不同
