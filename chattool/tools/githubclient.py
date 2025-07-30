import json
import logging
from typing import List, Dict, Optional, Any, Callable
import os
from github import Github
from github.GithubException import GithubException
from github.Repository import Repository
from github.ContentFile import ContentFile
from chattool.custom_logger import setup_logger
# 从chattool导入batch_executor相关功能
from chattool import batch_executor, batch_thread_executor


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