"""WordPress REST API client."""
from datetime import datetime
from typing import Iterator, List, Optional
from urllib.parse import urljoin

import requests

from .models import Post, Term


def _parse_post(data: dict) -> Post:
    return Post(
        id=data["id"],
        slug=data.get("slug", ""),
        title=data.get("title", {}).get("rendered", ""),
        content=data.get("content", {}).get("rendered", ""),
        excerpt=data.get("excerpt", {}).get("rendered", ""),
        date=datetime.fromisoformat(data["date"]),
        link=data.get("link", ""),
        author_id=data.get("author", 0),
        categories=data.get("categories", []),
        tags=data.get("tags", []),
    )


def _parse_term(data: dict) -> Term:
    return Term(
        id=data["id"],
        name=data.get("name", ""),
        slug=data.get("slug", ""),
        count=data.get("count", 0),
        description=data.get("description", ""),
        link=data.get("link", ""),
    )


class WordPressClient:
    """Read (and optionally write) content from a WordPress site via REST API."""

    def __init__(self, site_url: str, auth=None):
        self.base = site_url.rstrip("/") + "/wp-json/wp/v2/"
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "chattool-wordpress-explorer/1.0"
        if auth:
            self.session.auth = auth

    def _get(self, path: str, **params) -> requests.Response:
        resp = self.session.get(urljoin(self.base, path), params=params, timeout=15)
        resp.raise_for_status()
        return resp

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    def get_posts(
        self,
        search: Optional[str] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> List[Post]:
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        if categories:
            params["categories"] = ",".join(map(str, categories))
        if tags:
            params["tags"] = ",".join(map(str, tags))
        return [_parse_post(p) for p in self._get("posts", **params).json()]

    def iter_posts(
        self,
        search: Optional[str] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        per_page: int = 100,
    ) -> Iterator[Post]:
        """Lazily iterate all posts, handling pagination automatically."""
        page = 1
        while True:
            resp = self._get(
                "posts",
                page=page,
                per_page=per_page,
                **({} if not search else {"search": search}),
                **({} if not categories else {"categories": ",".join(map(str, categories))}),
                **({} if not tags else {"tags": ",".join(map(str, tags))}),
            )
            items = resp.json()
            if not items:
                break
            for item in items:
                yield _parse_post(item)
            total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
            if page >= total_pages:
                break
            page += 1

    def get_post(self, post_id: int) -> Post:
        return _parse_post(self._get(f"posts/{post_id}").json())

    def get_pages(self, per_page: int = 20) -> List[Post]:
        return [_parse_post(p) for p in self._get("pages", per_page=per_page).json()]

    # ------------------------------------------------------------------
    # Taxonomy
    # ------------------------------------------------------------------

    def get_categories(self, hide_empty: bool = True) -> List[Term]:
        return [_parse_term(t) for t in self._get("categories", per_page=100, hide_empty=hide_empty).json()]

    def get_tags(self, search: Optional[str] = None, per_page: int = 100) -> List[Term]:
        params = {"per_page": per_page}
        if search:
            params["search"] = search
        return [_parse_term(t) for t in self._get("tags", **params).json()]

    # ------------------------------------------------------------------
    # Write (requires auth)
    # ------------------------------------------------------------------

    def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
    ) -> Post:
        payload = {"title": title, "content": content, "status": status}
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags
        resp = self.session.post(urljoin(self.base, "posts"), json=payload, timeout=15)
        resp.raise_for_status()
        return _parse_post(resp.json())

    def update_post(self, post_id: int, **fields) -> Post:
        resp = self.session.post(urljoin(self.base, f"posts/{post_id}"), json=fields, timeout=15)
        resp.raise_for_status()
        return _parse_post(resp.json())
