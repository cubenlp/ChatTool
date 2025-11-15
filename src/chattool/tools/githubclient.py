import json
import logging
from typing import List, Dict, Optional, Any, Callable
import os
from github import Github
from github.GithubException import GithubException
from github.Repository import Repository
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest
from github.Issue import Issue
from github.Commit import Commit
from chattool.utils import setup_logger
from batch_executor import batch_executor, batch_thread_executor


class GitHubClient:
    def __init__(self, 
                 user_name: str,
                 token: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """初始化 GitHub 客户端
        
        Args:
            user_name: GitHub 用户名（必需）
            token: GitHub 访问令牌（可选，但推荐提供以避免速率限制）
            logger: 日志记录器（可选）
        """
        if not user_name:
            raise ValueError("user_name 不能为空")
        
        self.user_name = user_name
        self.logger = logger or setup_logger(self.__class__.__name__)
        token = token or os.getenv('GITHUB_ACCESS_TOKEN')
        # 初始化 PyGithub 客户端
        self.github = Github(token) if token else Github()
    
    def get_repositories(self) -> List[Dict]:
        """获取用户的所有仓库信息
        
        Returns:
            List[Dict]: 仓库信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repos = user.get_repos()
            
            repo_list = []
            for repo in repos:
                repo_info = {
                    "name": repo.name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
                }
                repo_list.append(repo_info)
            
            return repo_list
        except GithubException as e:
            self.logger.error(f"获取仓库列表失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库列表失败: {e}")
            return []
    
    def get_repository_readme(self, repo_name: str) -> Optional[str]:
        """获取指定仓库的 README.md 内容
        
        Args:
            repo_name: 仓库名称
            
        Returns:
            Optional[str]: README.md 内容
        """
        try:
            # 获取仓库对象
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            # 尝试获取 README 文件
            try:
                readme = repo.get_readme()
                return readme.decoded_content.decode('utf-8')
            except GithubException as e:
                # 如果 README 文件不存在，返回 None
                if e.status == 404:
                    self.logger.warning(f"仓库 {repo_name} 不存在 README 文件")
                    return None
                else:
                    raise e
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的 README 失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的 README 失败: {e}")
            return None
    
    def get_file_content(self, repo_name: str, file_path: str) -> Optional[str]:
        """获取指定仓库中指定文件的内容
        
        Args:
            repo_name: 仓库名称
            file_path: 文件路径（相对于仓库根目录）
            
        Returns:
            Optional[str]: 文件内容
        """
        try:
            # 获取仓库对象
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            # 获取文件内容
            file_content = repo.get_contents(file_path)
            
            # 确保获取的是文件而不是目录
            if isinstance(file_content, ContentFile):
                return file_content.decoded_content.decode('utf-8')
            else:
                self.logger.warning(f"路径 {file_path} 在仓库 {repo_name} 中不是文件")
                return None
        except GithubException as e:
            if e.status == 404:
                self.logger.warning(f"文件 {file_path} 在仓库 {repo_name} 中不存在")
                return None
            else:
                self.logger.error(f"获取文件 {file_path} 在仓库 {repo_name} 中失败: {e}")
                return None
        except Exception as e:
            self.logger.error(f"获取文件 {file_path} 在仓库 {repo_name} 中失败: {e}")
            return None
    
    def get_all_readmes(self) -> Dict[str, Optional[str]]:
        """获取用户所有仓库的 README.md 内容
        
        Returns:
            Dict[str, Optional[str]]: 仓库名到 README 内容的映射字典
        """
        # 先获取所有仓库
        repos = self.get_repositories()
        
        # 获取每个仓库的 README
        readmes = {}
        for repo_info in repos:
            repo_name = repo_info["name"]
            readme_content = self.get_repository_readme(repo_name)
            readmes[repo_name] = readme_content
            
        return readmes
    
    def get_all_readmes_concurrent(self, nproc: int = 5) -> Dict[str, Optional[str]]:
        """并发获取用户所有仓库的 README.md 内容
        
        Args:
            nproc: 并发进程数
            
        Returns:
            Dict[str, Optional[str]]: 仓库名到 README 内容的映射字典
        """
        # 先获取所有仓库
        repos = self.get_repositories()
        repo_names = [repo["name"] for repo in repos]
        
        # 定义获取单个仓库README的函数
        def _get_single_readme(repo_name: str) -> Optional[str]:
            return self.get_repository_readme(repo_name)
        
        # 使用batch_executor并发执行
        readme_contents = batch_thread_executor(
            items=repo_names,
            func=_get_single_readme,
            nproc=nproc,
            task_desc="获取仓库README文件",
            keep_order=True
        )
        
        # 构建结果字典
        readmes = dict(zip(repo_names, readme_contents))
        return readmes
    
    def get_files_content_concurrent(self, repo_name: str, file_paths: List[str], nproc: int = 5) -> Dict[str, Optional[str]]:
        """并发获取指定仓库中多个文件的内容
        
        Args:
            repo_name: 仓库名称
            file_paths: 文件路径列表（相对于仓库根目录）
            nproc: 并发进程数
            
        Returns:
            Dict[str, Optional[str]]: 文件路径到内容的映射字典
        """
        # 定义获取单个文件内容的函数
        def _get_single_file_content(file_path: str) -> Optional[str]:
            return self.get_file_content(repo_name, file_path)
        
        # 使用batch_executor并发执行
        file_contents = batch_thread_executor(
            items=file_paths,
            func=_get_single_file_content,
            nproc=nproc,
            task_desc=f"获取仓库{repo_name}中的文件",
            keep_order=True
        )
        
        # 构建结果字典
        files_content = dict(zip(file_paths, file_contents))
        return files_content
    
    def get_pull_requests(self, repo_name: str, state: str = "all", limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的Pull Request列表
        
        Args:
            repo_name: 仓库名称
            state: PR状态 ("open", "closed", "all")
            limit: 限制返回的PR数量
            
        Returns:
            List[Dict]: PR信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            prs = repo.get_pulls(state=state)
            
            pr_list = []
            count = 0
            for pr in prs:
                if limit and count >= limit:
                    break
                    
                pr_info = {
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body,
                    "state": pr.state,
                    "user": pr.user.login if pr.user else None,
                    "created_at": pr.created_at.isoformat() if pr.created_at else None,
                    "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                    "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                    "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                    "merge_commit_sha": pr.merge_commit_sha,
                    "head_sha": pr.head.sha if pr.head else None,
                    "base_sha": pr.base.sha if pr.base else None,
                    "url": pr.html_url,
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "changed_files": pr.changed_files
                }
                pr_list.append(pr_info)
                count += 1
            
            return pr_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的PR列表失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的PR列表失败: {e}")
            return []
    
    def get_pull_request_comments(self, repo_name: str, pr_number: int) -> Dict[str, List[Dict]]:
        """获取指定PR的所有评论和讨论
        
        Args:
            repo_name: 仓库名称
            pr_number: PR编号
            
        Returns:
            Dict[str, List[Dict]]: 包含issue评论、review评论和review的字典
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            result = {
                "issue_comments": [],
                "review_comments": [],
                "reviews": []
            }
            
            # 获取issue评论（PR的一般评论）
            for comment in pr.get_issue_comments():
                comment_info = {
                    "id": comment.id,
                    "user": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
                }
                result["issue_comments"].append(comment_info)
            
            # 获取review评论（代码行级别的评论）
            for comment in pr.get_review_comments():
                comment_info = {
                    "id": comment.id,
                    "user": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "path": comment.path,
                    "position": comment.position,
                    "original_position": comment.original_position,
                    "commit_id": comment.commit_id,
                    "original_commit_id": comment.original_commit_id,
                    "diff_hunk": comment.diff_hunk,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
                }
                result["review_comments"].append(comment_info)
            
            # 获取reviews
            for review in pr.get_reviews():
                review_info = {
                    "id": review.id,
                    "user": review.user.login if review.user else None,
                    "body": review.body,
                    "state": review.state,
                    "commit_id": review.commit_id,
                    "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None
                }
                result["reviews"].append(review_info)
            
            return result
        except GithubException as e:
            self.logger.error(f"获取PR {pr_number} 的评论失败: {e}")
            return {"issue_comments": [], "review_comments": [], "reviews": []}
        except Exception as e:
            self.logger.error(f"获取PR {pr_number} 的评论失败: {e}")
            return {"issue_comments": [], "review_comments": [], "reviews": []}
    
    def get_pull_request_files(self, repo_name: str, pr_number: int) -> List[Dict]:
        """获取指定PR的文件变更信息
        
        Args:
            repo_name: 仓库名称
            pr_number: PR编号
            
        Returns:
            List[Dict]: 文件变更信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            files_info = []
            for file in pr.get_files():
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "contents_url": file.contents_url,
                    "patch": file.patch if hasattr(file, 'patch') else None
                }
                files_info.append(file_info)
            
            return files_info
        except GithubException as e:
            self.logger.error(f"获取PR {pr_number} 的文件变更失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取PR {pr_number} 的文件变更失败: {e}")
            return []
    
    def get_issues(self, repo_name: str, state: str = "all", limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的Issue列表
        
        Args:
            repo_name: 仓库名称
            state: Issue状态 ("open", "closed", "all")
            limit: 限制返回的Issue数量
            
        Returns:
            List[Dict]: Issue信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            issues = repo.get_issues(state=state)
            
            issue_list = []
            count = 0
            for issue in issues:
                if limit and count >= limit:
                    break
                
                # 跳过Pull Request（GitHub API中PR也被当作Issue）
                if issue.pull_request:
                    continue
                    
                issue_info = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "user": issue.user.login if issue.user else None,
                    "assignee": issue.assignee.login if issue.assignee else None,
                    "assignees": [assignee.login for assignee in issue.assignees] if issue.assignees else [],
                    "labels": [label.name for label in issue.labels] if issue.labels else [],
                    "milestone": issue.milestone.title if issue.milestone else None,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "url": issue.html_url,
                    "comments_count": issue.comments
                }
                issue_list.append(issue_info)
                count += 1
            
            return issue_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
    
    def get_issue_comments(self, repo_name: str, issue_number: int) -> List[Dict]:
        """获取指定Issue的所有评论
        
        Args:
            repo_name: 仓库名称
            issue_number: Issue编号
            
        Returns:
            List[Dict]: 评论信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            
            comments_info = []
            for comment in issue.get_comments():
                comment_info = {
                    "id": comment.id,
                    "user": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
                }
                comments_info.append(comment_info)
            
            return comments_info
        except GithubException as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
    
    def get_commits(self, repo_name: str, since: Optional[str] = None, until: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的提交历史
        
        Args:
            repo_name: 仓库名称
            since: 开始时间（ISO格式字符串）
            until: 结束时间（ISO格式字符串）
            limit: 限制返回的提交数量
            
        Returns:
            List[Dict]: 提交信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            # 构建参数
            kwargs = {}
            if since:
                from datetime import datetime
                kwargs['since'] = datetime.fromisoformat(since.replace('Z', '+00:00'))
            if until:
                from datetime import datetime
                kwargs['until'] = datetime.fromisoformat(until.replace('Z', '+00:00'))
            
            commits = repo.get_commits(**kwargs)
            
            commit_list = []
            count = 0
            for commit in commits:
                if limit and count >= limit:
                    break
                    
                commit_info = {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name if commit.commit.author else None,
                        "email": commit.commit.author.email if commit.commit.author else None,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name if commit.commit.committer else None,
                        "email": commit.commit.committer.email if commit.commit.committer else None,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                    },
                    "url": commit.html_url,
                    "stats": {
                        "additions": commit.stats.additions if commit.stats else None,
                        "deletions": commit.stats.deletions if commit.stats else None,
                        "total": commit.stats.total if commit.stats else None
                    } if hasattr(commit, 'stats') and commit.stats else None
                }
                commit_list.append(commit_info)
                count += 1
            
            return commit_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
    
    def get_commit_details(self, repo_name: str, commit_sha: str) -> Optional[Dict]:
        """获取指定提交的详细信息
        
        Args:
            repo_name: 仓库名称
            commit_sha: 提交的SHA值
            
        Returns:
            Optional[Dict]: 提交详细信息
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            files_info = []
            for file in commit.files:
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch if hasattr(file, 'patch') else None
                }
                files_info.append(file_info)
            
            commit_detail = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name if commit.commit.author else None,
                    "email": commit.commit.author.email if commit.commit.author else None,
                    "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                },
                "committer": {
                    "name": commit.commit.committer.name if commit.commit.committer else None,
                    "email": commit.commit.committer.email if commit.commit.committer else None,
                    "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                },
                "url": commit.html_url,
                "stats": {
                    "additions": commit.stats.additions,
                    "deletions": commit.stats.deletions,
                    "total": commit.stats.total
                },
                "files": files_info
            }
            
            return commit_detail
        except GithubException as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
    
    def get_issues(self, repo_name: str, state: str = "all", limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的Issue列表
        
        Args:
            repo_name: 仓库名称
            state: Issue状态 ("open", "closed", "all")
            limit: 限制返回的Issue数量
            
        Returns:
            List[Dict]: Issue信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            issues = repo.get_issues(state=state)
            
            issue_list = []
            count = 0
            for issue in issues:
                if limit and count >= limit:
                    break
                
                # 跳过Pull Request（GitHub API中PR也被当作Issue）
                if issue.pull_request:
                    continue
                    
                issue_info = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "user": issue.user.login if issue.user else None,
                    "assignee": issue.assignee.login if issue.assignee else None,
                    "assignees": [assignee.login for assignee in issue.assignees] if issue.assignees else [],
                    "labels": [label.name for label in issue.labels] if issue.labels else [],
                    "milestone": issue.milestone.title if issue.milestone else None,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "url": issue.html_url,
                    "comments_count": issue.comments
                }
                issue_list.append(issue_info)
                count += 1
            
            return issue_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
    
    def get_issue_comments(self, repo_name: str, issue_number: int) -> List[Dict]:
        """获取指定Issue的所有评论
        
        Args:
            repo_name: 仓库名称
            issue_number: Issue编号
            
        Returns:
            List[Dict]: 评论信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            
            comments_info = []
            for comment in issue.get_comments():
                comment_info = {
                    "id": comment.id,
                    "user": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
                }
                comments_info.append(comment_info)
            
            return comments_info
        except GithubException as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
    
    def get_commits(self, repo_name: str, since: Optional[str] = None, until: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的提交历史
        
        Args:
            repo_name: 仓库名称
            since: 开始时间（ISO格式字符串）
            until: 结束时间（ISO格式字符串）
            limit: 限制返回的提交数量
            
        Returns:
            List[Dict]: 提交信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            # 构建参数
            kwargs = {}
            if since:
                from datetime import datetime
                kwargs['since'] = datetime.fromisoformat(since.replace('Z', '+00:00'))
            if until:
                from datetime import datetime
                kwargs['until'] = datetime.fromisoformat(until.replace('Z', '+00:00'))
            
            commits = repo.get_commits(**kwargs)
            
            commit_list = []
            count = 0
            for commit in commits:
                if limit and count >= limit:
                    break
                    
                commit_info = {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name if commit.commit.author else None,
                        "email": commit.commit.author.email if commit.commit.author else None,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name if commit.commit.committer else None,
                        "email": commit.commit.committer.email if commit.commit.committer else None,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                    },
                    "url": commit.html_url,
                    "stats": {
                        "additions": commit.stats.additions if commit.stats else None,
                        "deletions": commit.stats.deletions if commit.stats else None,
                        "total": commit.stats.total if commit.stats else None
                    } if hasattr(commit, 'stats') and commit.stats else None
                }
                commit_list.append(commit_info)
                count += 1
            
            return commit_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
    
    def get_commit_details(self, repo_name: str, commit_sha: str) -> Optional[Dict]:
        """获取指定提交的详细信息
        
        Args:
            repo_name: 仓库名称
            commit_sha: 提交的SHA值
            
        Returns:
            Optional[Dict]: 提交详细信息
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            files_info = []
            for file in commit.files:
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch if hasattr(file, 'patch') else None
                }
                files_info.append(file_info)
            
            commit_detail = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name if commit.commit.author else None,
                    "email": commit.commit.author.email if commit.commit.author else None,
                    "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                },
                "committer": {
                    "name": commit.commit.committer.name if commit.commit.committer else None,
                    "email": commit.commit.committer.email if commit.commit.committer else None,
                    "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                },
                "url": commit.html_url,
                "stats": {
                    "additions": commit.stats.additions,
                    "deletions": commit.stats.deletions,
                    "total": commit.stats.total
                },
                "files": files_info
            }
            
            return commit_detail
        except GithubException as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
    
    def get_issues(self, repo_name: str, state: str = "all", limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的Issue列表
        
        Args:
            repo_name: 仓库名称
            state: Issue状态 ("open", "closed", "all")
            limit: 限制返回的Issue数量
            
        Returns:
            List[Dict]: Issue信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            issues = repo.get_issues(state=state)
            
            issue_list = []
            count = 0
            for issue in issues:
                if limit and count >= limit:
                    break
                
                # 跳过Pull Request（GitHub API中PR也被当作Issue）
                if issue.pull_request:
                    continue
                    
                issue_info = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "user": issue.user.login if issue.user else None,
                    "assignee": issue.assignee.login if issue.assignee else None,
                    "assignees": [assignee.login for assignee in issue.assignees] if issue.assignees else [],
                    "labels": [label.name for label in issue.labels] if issue.labels else [],
                    "milestone": issue.milestone.title if issue.milestone else None,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "url": issue.html_url,
                    "comments_count": issue.comments
                }
                issue_list.append(issue_info)
                count += 1
            
            return issue_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
    
    def get_issue_comments(self, repo_name: str, issue_number: int) -> List[Dict]:
        """获取指定Issue的所有评论
        
        Args:
            repo_name: 仓库名称
            issue_number: Issue编号
            
        Returns:
            List[Dict]: 评论信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            
            comments_info = []
            for comment in issue.get_comments():
                comment_info = {
                    "id": comment.id,
                    "user": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
                }
                comments_info.append(comment_info)
            
            return comments_info
        except GithubException as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
    
    def get_commits(self, repo_name: str, since: Optional[str] = None, until: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的提交历史
        
        Args:
            repo_name: 仓库名称
            since: 开始时间（ISO格式字符串）
            until: 结束时间（ISO格式字符串）
            limit: 限制返回的提交数量
            
        Returns:
            List[Dict]: 提交信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            # 构建参数
            kwargs = {}
            if since:
                from datetime import datetime
                kwargs['since'] = datetime.fromisoformat(since.replace('Z', '+00:00'))
            if until:
                from datetime import datetime
                kwargs['until'] = datetime.fromisoformat(until.replace('Z', '+00:00'))
            
            commits = repo.get_commits(**kwargs)
            
            commit_list = []
            count = 0
            for commit in commits:
                if limit and count >= limit:
                    break
                    
                commit_info = {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name if commit.commit.author else None,
                        "email": commit.commit.author.email if commit.commit.author else None,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name if commit.commit.committer else None,
                        "email": commit.commit.committer.email if commit.commit.committer else None,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                    },
                    "url": commit.html_url,
                    "stats": {
                        "additions": commit.stats.additions if commit.stats else None,
                        "deletions": commit.stats.deletions if commit.stats else None,
                        "total": commit.stats.total if commit.stats else None
                    } if hasattr(commit, 'stats') and commit.stats else None
                }
                commit_list.append(commit_info)
                count += 1
            
            return commit_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
    
    def get_commit_details(self, repo_name: str, commit_sha: str) -> Optional[Dict]:
        """获取指定提交的详细信息
        
        Args:
            repo_name: 仓库名称
            commit_sha: 提交的SHA值
            
        Returns:
            Optional[Dict]: 提交详细信息
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            files_info = []
            for file in commit.files:
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch if hasattr(file, 'patch') else None
                }
                files_info.append(file_info)
            
            commit_detail = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name if commit.commit.author else None,
                    "email": commit.commit.author.email if commit.commit.author else None,
                    "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                },
                "committer": {
                    "name": commit.commit.committer.name if commit.commit.committer else None,
                    "email": commit.commit.committer.email if commit.commit.committer else None,
                    "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                },
                "url": commit.html_url,
                "stats": {
                    "additions": commit.stats.additions,
                    "deletions": commit.stats.deletions,
                    "total": commit.stats.total
                },
                "files": files_info
            }
            
            return commit_detail
        except GithubException as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
    
    def get_issues(self, repo_name: str, state: str = "all", limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的Issue列表
        
        Args:
            repo_name: 仓库名称
            state: Issue状态 ("open", "closed", "all")
            limit: 限制返回的Issue数量
            
        Returns:
            List[Dict]: Issue信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            issues = repo.get_issues(state=state)
            
            issue_list = []
            count = 0
            for issue in issues:
                if limit and count >= limit:
                    break
                
                # 跳过Pull Request（GitHub API中PR也被当作Issue）
                if issue.pull_request:
                    continue
                    
                issue_info = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "user": issue.user.login if issue.user else None,
                    "assignee": issue.assignee.login if issue.assignee else None,
                    "assignees": [assignee.login for assignee in issue.assignees] if issue.assignees else [],
                    "labels": [label.name for label in issue.labels] if issue.labels else [],
                    "milestone": issue.milestone.title if issue.milestone else None,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "url": issue.html_url,
                    "comments_count": issue.comments
                }
                issue_list.append(issue_info)
                count += 1
            
            return issue_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
    
    def get_issue_comments(self, repo_name: str, issue_number: int) -> List[Dict]:
        """获取指定Issue的所有评论
        
        Args:
            repo_name: 仓库名称
            issue_number: Issue编号
            
        Returns:
            List[Dict]: 评论信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            
            comments_info = []
            for comment in issue.get_comments():
                comment_info = {
                    "id": comment.id,
                    "user": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
                }
                comments_info.append(comment_info)
            
            return comments_info
        except GithubException as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
    
    def get_commits(self, repo_name: str, since: Optional[str] = None, until: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的提交历史
        
        Args:
            repo_name: 仓库名称
            since: 开始时间（ISO格式字符串）
            until: 结束时间（ISO格式字符串）
            limit: 限制返回的提交数量
            
        Returns:
            List[Dict]: 提交信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            # 构建参数
            kwargs = {}
            if since:
                from datetime import datetime
                kwargs['since'] = datetime.fromisoformat(since.replace('Z', '+00:00'))
            if until:
                from datetime import datetime
                kwargs['until'] = datetime.fromisoformat(until.replace('Z', '+00:00'))
            
            commits = repo.get_commits(**kwargs)
            
            commit_list = []
            count = 0
            for commit in commits:
                if limit and count >= limit:
                    break
                    
                commit_info = {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name if commit.commit.author else None,
                        "email": commit.commit.author.email if commit.commit.author else None,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name if commit.commit.committer else None,
                        "email": commit.commit.committer.email if commit.commit.committer else None,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                    },
                    "url": commit.html_url,
                    "stats": {
                        "additions": commit.stats.additions if commit.stats else None,
                        "deletions": commit.stats.deletions if commit.stats else None,
                        "total": commit.stats.total if commit.stats else None
                    } if hasattr(commit, 'stats') and commit.stats else None
                }
                commit_list.append(commit_info)
                count += 1
            
            return commit_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
    
    def get_commit_details(self, repo_name: str, commit_sha: str) -> Optional[Dict]:
        """获取指定提交的详细信息
        
        Args:
            repo_name: 仓库名称
            commit_sha: 提交的SHA值
            
        Returns:
            Optional[Dict]: 提交详细信息
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            files_info = []
            for file in commit.files:
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch if hasattr(file, 'patch') else None
                }
                files_info.append(file_info)
            
            commit_detail = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name if commit.commit.author else None,
                    "email": commit.commit.author.email if commit.commit.author else None,
                    "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                },
                "committer": {
                    "name": commit.commit.committer.name if commit.commit.committer else None,
                    "email": commit.commit.committer.email if commit.commit.committer else None,
                    "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                },
                "url": commit.html_url,
                "stats": {
                    "additions": commit.stats.additions,
                    "deletions": commit.stats.deletions,
                    "total": commit.stats.total
                },
                "files": files_info
            }
            
            return commit_detail
        except GithubException as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
    
    def get_issues(self, repo_name: str, state: str = "all", limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的Issue列表
        
        Args:
            repo_name: 仓库名称
            state: Issue状态 ("open", "closed", "all")
            limit: 限制返回的Issue数量
            
        Returns:
            List[Dict]: Issue信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            issues = repo.get_issues(state=state)
            
            issue_list = []
            count = 0
            for issue in issues:
                if limit and count >= limit:
                    break
                
                # 跳过Pull Request（GitHub API中PR也被当作Issue）
                if issue.pull_request:
                    continue
                    
                issue_info = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "user": issue.user.login if issue.user else None,
                    "assignee": issue.assignee.login if issue.assignee else None,
                    "assignees": [assignee.login for assignee in issue.assignees] if issue.assignees else [],
                    "labels": [label.name for label in issue.labels] if issue.labels else [],
                    "milestone": issue.milestone.title if issue.milestone else None,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "url": issue.html_url,
                    "comments_count": issue.comments
                }
                issue_list.append(issue_info)
                count += 1
            
            return issue_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
    
    def get_issue_comments(self, repo_name: str, issue_number: int) -> List[Dict]:
        """获取指定Issue的所有评论
        
        Args:
            repo_name: 仓库名称
            issue_number: Issue编号
            
        Returns:
            List[Dict]: 评论信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            
            comments_info = []
            for comment in issue.get_comments():
                comment_info = {
                    "id": comment.id,
                    "user": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
                }
                comments_info.append(comment_info)
            
            return comments_info
        except GithubException as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
    
    def get_commits(self, repo_name: str, since: Optional[str] = None, until: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的提交历史
        
        Args:
            repo_name: 仓库名称
            since: 开始时间（ISO格式字符串）
            until: 结束时间（ISO格式字符串）
            limit: 限制返回的提交数量
            
        Returns:
            List[Dict]: 提交信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            # 构建参数
            kwargs = {}
            if since:
                from datetime import datetime
                kwargs['since'] = datetime.fromisoformat(since.replace('Z', '+00:00'))
            if until:
                from datetime import datetime
                kwargs['until'] = datetime.fromisoformat(until.replace('Z', '+00:00'))
            
            commits = repo.get_commits(**kwargs)
            
            commit_list = []
            count = 0
            for commit in commits:
                if limit and count >= limit:
                    break
                    
                commit_info = {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name if commit.commit.author else None,
                        "email": commit.commit.author.email if commit.commit.author else None,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name if commit.commit.committer else None,
                        "email": commit.commit.committer.email if commit.commit.committer else None,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                    },
                    "url": commit.html_url,
                    "stats": {
                        "additions": commit.stats.additions if commit.stats else None,
                        "deletions": commit.stats.deletions if commit.stats else None,
                        "total": commit.stats.total if commit.stats else None
                    } if hasattr(commit, 'stats') and commit.stats else None
                }
                commit_list.append(commit_info)
                count += 1
            
            return commit_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
    
    def get_commit_details(self, repo_name: str, commit_sha: str) -> Optional[Dict]:
        """获取指定提交的详细信息
        
        Args:
            repo_name: 仓库名称
            commit_sha: 提交的SHA值
            
        Returns:
            Optional[Dict]: 提交详细信息
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            files_info = []
            for file in commit.files:
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch if hasattr(file, 'patch') else None
                }
                files_info.append(file_info)
            
            commit_detail = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name if commit.commit.author else None,
                    "email": commit.commit.author.email if commit.commit.author else None,
                    "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                },
                "committer": {
                    "name": commit.commit.committer.name if commit.commit.committer else None,
                    "email": commit.commit.committer.email if commit.commit.committer else None,
                    "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                },
                "url": commit.html_url,
                "stats": {
                    "additions": commit.stats.additions,
                    "deletions": commit.stats.deletions,
                    "total": commit.stats.total
                },
                "files": files_info
            }
            
            return commit_detail
        except GithubException as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
    
    def get_issues(self, repo_name: str, state: str = "all", limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的Issue列表
        
        Args:
            repo_name: 仓库名称
            state: Issue状态 ("open", "closed", "all")
            limit: 限制返回的Issue数量
            
        Returns:
            List[Dict]: Issue信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            issues = repo.get_issues(state=state)
            
            issue_list = []
            count = 0
            for issue in issues:
                if limit and count >= limit:
                    break
                
                # 跳过Pull Request（GitHub API中PR也被当作Issue）
                if issue.pull_request:
                    continue
                    
                issue_info = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "user": issue.user.login if issue.user else None,
                    "assignee": issue.assignee.login if issue.assignee else None,
                    "assignees": [assignee.login for assignee in issue.assignees] if issue.assignees else [],
                    "labels": [label.name for label in issue.labels] if issue.labels else [],
                    "milestone": issue.milestone.title if issue.milestone else None,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "url": issue.html_url,
                    "comments_count": issue.comments
                }
                issue_list.append(issue_info)
                count += 1
            
            return issue_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
    
    def get_issue_comments(self, repo_name: str, issue_number: int) -> List[Dict]:
        """获取指定Issue的所有评论
        
        Args:
            repo_name: 仓库名称
            issue_number: Issue编号
            
        Returns:
            List[Dict]: 评论信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            
            comments_info = []
            for comment in issue.get_comments():
                comment_info = {
                    "id": comment.id,
                    "user": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
                }
                comments_info.append(comment_info)
            
            return comments_info
        except GithubException as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
    
    def get_commits(self, repo_name: str, since: Optional[str] = None, until: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的提交历史
        
        Args:
            repo_name: 仓库名称
            since: 开始时间（ISO格式字符串）
            until: 结束时间（ISO格式字符串）
            limit: 限制返回的提交数量
            
        Returns:
            List[Dict]: 提交信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            # 构建参数
            kwargs = {}
            if since:
                from datetime import datetime
                kwargs['since'] = datetime.fromisoformat(since.replace('Z', '+00:00'))
            if until:
                from datetime import datetime
                kwargs['until'] = datetime.fromisoformat(until.replace('Z', '+00:00'))
            
            commits = repo.get_commits(**kwargs)
            
            commit_list = []
            count = 0
            for commit in commits:
                if limit and count >= limit:
                    break
                    
                commit_info = {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name if commit.commit.author else None,
                        "email": commit.commit.author.email if commit.commit.author else None,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name if commit.commit.committer else None,
                        "email": commit.commit.committer.email if commit.commit.committer else None,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                    },
                    "url": commit.html_url,
                    "stats": {
                        "additions": commit.stats.additions if commit.stats else None,
                        "deletions": commit.stats.deletions if commit.stats else None,
                        "total": commit.stats.total if commit.stats else None
                    } if hasattr(commit, 'stats') and commit.stats else None
                }
                commit_list.append(commit_info)
                count += 1
            
            return commit_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
    
    def get_commit_details(self, repo_name: str, commit_sha: str) -> Optional[Dict]:
        """获取指定提交的详细信息
        
        Args:
            repo_name: 仓库名称
            commit_sha: 提交的SHA值
            
        Returns:
            Optional[Dict]: 提交详细信息
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            files_info = []
            for file in commit.files:
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch if hasattr(file, 'patch') else None
                }
                files_info.append(file_info)
            
            commit_detail = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name if commit.commit.author else None,
                    "email": commit.commit.author.email if commit.commit.author else None,
                    "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                },
                "committer": {
                    "name": commit.commit.committer.name if commit.commit.committer else None,
                    "email": commit.commit.committer.email if commit.commit.committer else None,
                    "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                },
                "url": commit.html_url,
                "stats": {
                    "additions": commit.stats.additions,
                    "deletions": commit.stats.deletions,
                    "total": commit.stats.total
                },
                "files": files_info
            }
            
            return commit_detail
        except GithubException as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
    
    def get_issues(self, repo_name: str, state: str = "all", limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的Issue列表
        
        Args:
            repo_name: 仓库名称
            state: Issue状态 ("open", "closed", "all")
            limit: 限制返回的Issue数量
            
        Returns:
            List[Dict]: Issue信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            issues = repo.get_issues(state=state)
            
            issue_list = []
            count = 0
            for issue in issues:
                if limit and count >= limit:
                    break
                
                # 跳过Pull Request（GitHub API中PR也被当作Issue）
                if issue.pull_request:
                    continue
                    
                issue_info = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "user": issue.user.login if issue.user else None,
                    "assignee": issue.assignee.login if issue.assignee else None,
                    "assignees": [assignee.login for assignee in issue.assignees] if issue.assignees else [],
                    "labels": [label.name for label in issue.labels] if issue.labels else [],
                    "milestone": issue.milestone.title if issue.milestone else None,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "url": issue.html_url,
                    "comments_count": issue.comments
                }
                issue_list.append(issue_info)
                count += 1
            
            return issue_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的Issue列表失败: {e}")
            return []
    
    def get_issue_comments(self, repo_name: str, issue_number: int) -> List[Dict]:
        """获取指定Issue的所有评论
        
        Args:
            repo_name: 仓库名称
            issue_number: Issue编号
            
        Returns:
            List[Dict]: 评论信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            
            comments_info = []
            for comment in issue.get_comments():
                comment_info = {
                    "id": comment.id,
                    "user": comment.user.login if comment.user else None,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
                }
                comments_info.append(comment_info)
            
            return comments_info
        except GithubException as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取Issue {issue_number} 的评论失败: {e}")
            return []
    
    def get_commits(self, repo_name: str, since: Optional[str] = None, until: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """获取指定仓库的提交历史
        
        Args:
            repo_name: 仓库名称
            since: 开始时间（ISO格式字符串）
            until: 结束时间（ISO格式字符串）
            limit: 限制返回的提交数量
            
        Returns:
            List[Dict]: 提交信息列表
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            
            # 构建参数
            kwargs = {}
            if since:
                from datetime import datetime
                kwargs['since'] = datetime.fromisoformat(since.replace('Z', '+00:00'))
            if until:
                from datetime import datetime
                kwargs['until'] = datetime.fromisoformat(until.replace('Z', '+00:00'))
            
            commits = repo.get_commits(**kwargs)
            
            commit_list = []
            count = 0
            for commit in commits:
                if limit and count >= limit:
                    break
                    
                commit_info = {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name if commit.commit.author else None,
                        "email": commit.commit.author.email if commit.commit.author else None,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name if commit.commit.committer else None,
                        "email": commit.commit.committer.email if commit.commit.committer else None,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                    },
                    "url": commit.html_url,
                    "stats": {
                        "additions": commit.stats.additions if commit.stats else None,
                        "deletions": commit.stats.deletions if commit.stats else None,
                        "total": commit.stats.total if commit.stats else None
                    } if hasattr(commit, 'stats') and commit.stats else None
                }
                commit_list.append(commit_info)
                count += 1
            
            return commit_list
        except GithubException as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取仓库 {repo_name} 的提交历史失败: {e}")
            return []
    
    def get_commit_details(self, repo_name: str, commit_sha: str) -> Optional[Dict]:
        """获取指定提交的详细信息
        
        Args:
            repo_name: 仓库名称
            commit_sha: 提交的SHA值
            
        Returns:
            Optional[Dict]: 提交详细信息
        """
        try:
            user = self.github.get_user(self.user_name)
            repo = user.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            files_info = []
            for file in commit.files:
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch if hasattr(file, 'patch') else None
                }
                files_info.append(file_info)
            
            commit_detail = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name if commit.commit.author else None,
                    "email": commit.commit.author.email if commit.commit.author else None,
                    "date": commit.commit.author.date.isoformat() if commit.commit.author and commit.commit.author.date else None
                },
                "committer": {
                    "name": commit.commit.committer.name if commit.commit.committer else None,
                    "email": commit.commit.committer.email if commit.commit.committer else None,
                    "date": commit.commit.committer.date.isoformat() if commit.commit.committer and commit.commit.committer.date else None
                },
                "url": commit.html_url,
                "stats": {
                    "additions": commit.stats.additions,
                    "deletions": commit.stats.deletions,
                    "total": commit.stats.total
                },
                "files": files_info
            }
            
            return commit_detail
        except GithubException as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取提交 {commit_sha} 的详细信息失败: {e}")
            return None