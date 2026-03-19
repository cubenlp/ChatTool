"""GitHub explore data models."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Repo:
    full_name: str
    description: Optional[str]
    url: str
    stars: int
    forks: int
    language: Optional[str]
    topics: list = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pushed_at: Optional[datetime] = None

    @property
    def owner(self) -> str:
        return self.full_name.split("/")[0]

    @property
    def name(self) -> str:
        return self.full_name.split("/")[1]

    def __repr__(self):
        return f"Repo({self.full_name!r}, stars={self.stars})"


@dataclass
class Issue:
    number: int
    title: str
    state: str
    url: str
    created_at: Optional[datetime] = None
    labels: list = field(default_factory=list)

    def __repr__(self):
        return f"Issue(#{self.number}, {self.title!r})"
