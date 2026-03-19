"""GitHub explore client."""
import os
from datetime import datetime, timezone, timedelta
from typing import Iterator, List, Optional

from .models import Repo, Issue


def _to_repo(r) -> Repo:
    return Repo(
        full_name=r.full_name,
        description=r.description,
        url=r.html_url,
        stars=r.stargazers_count,
        forks=r.forks_count,
        language=r.language,
        topics=list(r.topics) if r.topics else [],
        created_at=r.created_at,
        updated_at=r.updated_at,
        pushed_at=r.pushed_at,
    )


def _to_issue(i) -> Issue:
    return Issue(
        number=i.number,
        title=i.title,
        state=i.state,
        url=i.html_url,
        created_at=i.created_at,
        labels=[l.name for l in i.labels],
    )


class GithubExplorer:
    """Explore GitHub repos, issues and trending via REST API v3."""

    def __init__(self, token: Optional[str] = None):
        from github import Github
        token = token or os.getenv("GITHUB_ACCESS_TOKEN")
        self._gh = Github(token) if token else Github()

    def search_repos(
        self,
        query: str,
        sort: str = "stars",
        max_results: int = 10,
    ) -> List[Repo]:
        results = self._gh.search_repositories(query, sort=sort)
        return [_to_repo(r) for r in results[:max_results]]

    def get_repo(self, full_name: str) -> Repo:
        return _to_repo(self._gh.get_repo(full_name))

    def get_readme(self, full_name: str) -> str:
        """Return decoded README markdown text."""
        repo = self._gh.get_repo(full_name)
        return repo.get_readme().decoded_content.decode("utf-8")

    def get_releases(self, full_name: str, n: int = 5) -> List[dict]:
        repo = self._gh.get_repo(full_name)
        return [
            {"tag": r.tag_name, "name": r.title, "published_at": r.published_at, "url": r.html_url}
            for r in repo.get_releases()[:n]
        ]

    def get_issues(
        self,
        full_name: str,
        state: str = "open",
        n: int = 10,
    ) -> List[Issue]:
        repo = self._gh.get_repo(full_name)
        return [_to_issue(i) for i in repo.get_issues(state=state)[:n]]

    def trending(
        self,
        language: Optional[str] = None,
        since_days: int = 7,
        n: int = 10,
    ) -> List[Repo]:
        """Simulate trending: recently created repos sorted by stars."""
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).date().isoformat()
        query = f"created:>{since}"
        if language:
            query += f" language:{language}"
        return self.search_repos(query, sort="stars", max_results=n)

    def get_languages(self, full_name: str) -> dict:
        """Return language breakdown (bytes) for a repo."""
        return self._gh.get_repo(full_name).get_languages()

    def get_commit_activity(self, full_name: str) -> list:
        """Return weekly commit activity for the past 52 weeks."""
        return [
            {"week": s.week, "total": s.total, "days": s.days}
            for s in self._gh.get_repo(full_name).get_stats_commit_activity()
        ]

    def rate_limit(self) -> dict:
        """Return current rate limit status for core and search."""
        rl = self._gh.get_rate_limit()
        return {
            "core": {"limit": rl.core.limit, "remaining": rl.core.remaining, "reset": rl.core.reset},
            "search": {"limit": rl.search.limit, "remaining": rl.search.remaining, "reset": rl.search.reset},
        }
