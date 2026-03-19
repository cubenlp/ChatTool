"""WordPress explore data models."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Post:
    id: int
    slug: str
    title: str
    content: str
    excerpt: str
    date: datetime
    link: str
    author_id: int
    categories: list = field(default_factory=list)
    tags: list = field(default_factory=list)

    def __repr__(self):
        return f"Post({self.id}, {self.title!r})"


@dataclass
class Term:
    id: int
    name: str
    slug: str
    count: int
    description: str
    link: str

    def __repr__(self):
        return f"Term({self.id}, {self.name!r})"
