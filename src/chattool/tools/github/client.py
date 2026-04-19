from __future__ import annotations

import logging
from typing import Dict, List, Optional

from chattool.tools.github.api import get_client, resolve_token
from chattool.tools.github.render import derive_repo_capabilities
from chattool.tools.github.requests import (
    get_pr_checks,
    get_pr_list,
    get_pr_view,
    get_repo_permissions,
    get_run_view,
    patch_pr_edit,
    post_pr_comment,
    post_pr_create,
    post_pr_merge,
)
from chattool.utils import setup_logger


class GitHubClient:
    def __init__(
        self,
        user_name: str,
        token: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if not user_name:
            raise ValueError("user_name 不能为空")
        self.user_name = user_name
        self.logger = logger or setup_logger(self.__class__.__name__)
        self.github = get_client(token)

    def get_repositories(self) -> List[Dict]:
        user = self.github.get_user(self.user_name)
        items: List[Dict] = []
        for repo in user.get_repos():
            items.append(
                {
                    "name": repo.name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                }
            )
        return items

    def get_repository_readme(self, repo_name: str) -> Optional[str]:
        repo = self.github.get_user(self.user_name).get_repo(repo_name)
        try:
            return repo.get_readme().decoded_content.decode("utf-8")
        except Exception:
            return None

    def get_file_content(self, repo_name: str, file_path: str) -> Optional[str]:
        repo = self.github.get_user(self.user_name).get_repo(repo_name)
        try:
            content = repo.get_contents(file_path)
        except Exception:
            return None
        decoded = getattr(content, "decoded_content", None)
        if decoded is None:
            return None
        return decoded.decode("utf-8")

    def get_pull_requests(
        self,
        repo_name: str,
        state: str = "open",
        limit: Optional[int] = None,
    ) -> List[Dict]:
        return get_pr_list(self.github, f"{self.user_name}/{repo_name}", state, limit or 20)

    def get_pr_view(self, repo: str, number: int) -> Dict:
        return get_pr_view(self.github, repo, number)

    def get_pr_checks(
        self,
        repo: str,
        number: int,
        check_limit: int = 20,
        workflow_limit: int = 10,
    ) -> Dict:
        return get_pr_checks(self.github, repo, number, check_limit, workflow_limit)

    def post_pr_create(
        self,
        repo: str,
        *,
        base: str,
        head: str,
        title: str,
        body: str = "",
    ) -> Dict:
        return post_pr_create(self.github, repo, base, head, title, body)

    def post_pr_comment(self, repo: str, number: int, body: str) -> Dict:
        return post_pr_comment(self.github, repo, number, body)

    def post_pr_merge(
        self,
        repo: str,
        number: int,
        *,
        method: str = "merge",
        title: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Dict:
        return post_pr_merge(self.github, repo, number, method, title, message)

    def patch_pr_edit(
        self,
        repo: str,
        number: int,
        *,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        base: Optional[str] = None,
    ) -> Dict:
        return patch_pr_edit(
            self.github,
            repo,
            number,
            title=title,
            body=body,
            state=state,
            base=base,
        )

    def get_repo_perms(self, repo: str, token: Optional[str] = None) -> Dict:
        resolved_token = resolve_token(token)
        payload = get_repo_permissions(repo, resolved_token)
        permissions = payload.get("permissions") or {}
        return {
            "repo": payload.get("full_name") or repo,
            "private": payload.get("private"),
            "visibility": payload.get("visibility"),
            "permissions": permissions,
            "capabilities": derive_repo_capabilities(permissions),
        }

    def get_run_view(
        self,
        repo: str,
        run_id: int,
        token: Optional[str] = None,
        job_limit: int = 50,
    ) -> Dict:
        return get_run_view(repo, run_id, resolve_token(token), job_limit)
