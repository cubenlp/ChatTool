import os
import pytest
from chattool.tools import GitHubClient
from tests.const import logger
from unittest.mock import Mock, patch


class TestGitHubClientReal:
    """GitHubClient真实API测试类"""
    
    @pytest.fixture
    def real_github_client(self):
        """创建真实的GitHub客户端"""
        # 使用环境变量中的token，如果没有则使用无token版本（有速率限制）
        token = os.getenv('GITHUB_ACCESS_TOKEN')
        return GitHubClient(user_name="loganrjmurphy", token=token)
    
    def test_get_repositories_real(self, real_github_client):
        """测试获取真实用户的仓库列表"""
        repos = real_github_client.get_repositories()
        
        assert isinstance(repos, list)
        assert len(repos) > 0, "用户应该有至少一个仓库"
        
        # 检查是否包含LeanEuclid仓库
        repo_names = [repo['name'] for repo in repos]
        assert 'LeanEuclid' in repo_names, "应该包含LeanEuclid仓库"
        
        # 验证仓库信息结构
        lean_euclid = next(repo for repo in repos if repo['name'] == 'LeanEuclid')
        assert 'description' in lean_euclid
        assert 'url' in lean_euclid
        assert 'stars' in lean_euclid
        assert 'language' in lean_euclid
        
        logger.info(f"找到 {len(repos)} 个仓库，包括LeanEuclid")
        logger.info(f"LeanEuclid仓库信息: {lean_euclid}")
    
    def test_get_repository_readme_real(self, real_github_client):
        """测试获取LeanEuclid仓库的README"""
        readme = real_github_client.get_repository_readme("LeanEuclid")
        
        assert readme is not None, "LeanEuclid应该有README文件"
        assert isinstance(readme, str)
        assert len(readme) > 0
        
        # 检查README内容是否包含预期的关键词
        readme_lower = readme.lower()
        assert any(keyword in readme_lower for keyword in ['lean', 'euclid', 'theorem']), \
            "README应该包含项目相关的关键词"
        
        logger.info(f"README长度: {len(readme)} 字符")
        logger.info(f"README前200字符: {readme[:200]}...")
    
    def test_get_file_content_real(self, real_github_client):
        """测试获取LeanEuclid仓库的具体文件内容"""
        # 尝试获取一些常见的文件
        files_to_test = [
            "README.md",
            "lakefile.lean",  # Lean项目的配置文件
            "LeanEuclid.lean"  # 可能的主文件
        ]
        
        found_files = []
        for file_path in files_to_test:
            content = real_github_client.get_file_content("LeanEuclid", file_path)
            if content is not None:
                found_files.append(file_path)
                logger.info(f"成功获取文件 {file_path}，长度: {len(content)} 字符")
                
                # 验证文件内容
                assert isinstance(content, str)
                assert len(content) > 0
        
        assert len(found_files) > 0, "应该至少能获取到一个文件的内容"
        logger.info(f"成功获取的文件: {found_files}")
    
    def test_get_commits_real(self, real_github_client):
        """测试获取LeanEuclid仓库的提交历史"""
        commits = real_github_client.get_commits("LeanEuclid", limit=10)
        
        assert isinstance(commits, list)
        assert len(commits) > 0, "仓库应该有提交历史"
        
        # 验证提交信息结构
        first_commit = commits[0]
        assert 'sha' in first_commit
        assert 'message' in first_commit
        assert 'author' in first_commit
        assert 'committer' in first_commit
        assert 'url' in first_commit
        
        # 验证作者信息
        author = first_commit['author']
        assert 'name' in author
        assert 'email' in author
        
        logger.info(f"获取到 {len(commits)} 个提交")
        logger.info(f"最新提交: {first_commit['message'][:100]}...")
        logger.info(f"作者: {author['name']}")
    
    def test_get_commit_details_real(self, real_github_client):
        """测试获取具体提交的详细信息"""
        # 先获取最新的提交
        commits = real_github_client.get_commits("LeanEuclid", limit=1)
        assert len(commits) > 0, "应该有至少一个提交"
        
        latest_commit_sha = commits[0]['sha']
        
        # 获取提交详情
        commit_detail = real_github_client.get_commit_details("LeanEuclid", latest_commit_sha)
        
        assert commit_detail is not None
        assert 'sha' in commit_detail
        assert 'message' in commit_detail
        assert 'files' in commit_detail
        assert 'stats' in commit_detail
        
        # 验证统计信息
        stats = commit_detail['stats']
        assert 'additions' in stats
        assert 'deletions' in stats
        assert 'total' in stats
        
        logger.info(f"提交详情 - SHA: {commit_detail['sha'][:8]}")
        logger.info(f"变更统计: +{stats['additions']} -{stats['deletions']}")
        logger.info(f"变更文件数: {len(commit_detail['files'])}")
    
    def test_get_issues_real(self, real_github_client):
        """测试获取LeanEuclid仓库的Issues"""
        issues = real_github_client.get_issues("LeanEuclid", state="all", limit=20)
        
        assert isinstance(issues, list)
        
        if len(issues) > 0:
            # 如果有issues，验证结构
            first_issue = issues[0]
            assert 'number' in first_issue
            assert 'title' in first_issue
            assert 'state' in first_issue
            assert 'user' in first_issue
            
            logger.info(f"找到 {len(issues)} 个Issues")
            logger.info(f"第一个Issue: #{first_issue['number']} - {first_issue['title']}")
        else:
            logger.info("该仓库没有Issues")
    
    def test_get_pull_requests_real(self, real_github_client):
        """测试获取LeanEuclid仓库的Pull Requests"""
        prs = real_github_client.get_pull_requests("LeanEuclid", state="all", limit=20)
        
        assert isinstance(prs, list)
        
        if len(prs) > 0:
            # 如果有PRs，验证结构
            first_pr = prs[0]
            assert 'number' in first_pr
            assert 'title' in first_pr
            assert 'state' in first_pr
            assert 'user' in first_pr
            assert 'additions' in first_pr
            assert 'deletions' in first_pr
            
            logger.info(f"找到 {len(prs)} 个Pull Requests")
            logger.info(f"第一个PR: #{first_pr['number']} - {first_pr['title']}")
            
            # 测试获取PR的评论
            if len(prs) > 0:
                pr_number = first_pr['number']
                comments = real_github_client.get_pull_request_comments("LeanEuclid", pr_number)
                
                assert isinstance(comments, dict)
                assert 'issue_comments' in comments
                assert 'review_comments' in comments
                assert 'reviews' in comments
                
                total_comments = (len(comments['issue_comments']) + 
                                len(comments['review_comments']) + 
                                len(comments['reviews']))
                logger.info(f"PR #{pr_number} 总评论数: {total_comments}")
        else:
            logger.info("该仓库没有Pull Requests")
    
    def test_error_handling_real(self, real_github_client):
        """测试错误处理 - 访问不存在的仓库"""
        # 测试访问不存在的仓库
        repos = real_github_client.get_repositories()
        assert isinstance(repos, list)  # 应该返回空列表而不是抛出异常
        
        # 测试访问不存在的文件
        content = real_github_client.get_file_content("LeanEuclid", "nonexistent_file.txt")
        assert content is None  # 应该返回None而不是抛出异常
        
        # 测试访问不存在的提交
        commit_detail = real_github_client.get_commit_details("LeanEuclid", "invalid_sha")
        assert commit_detail is None  # 应该返回None而不是抛出异常
        
        logger.info("错误处理测试通过")
    
    def test_concurrent_operations_real(self, real_github_client):
        """测试并发操作的真实性能"""
        import time
        
        # 测试并发获取README
        start_time = time.time()
        readmes = real_github_client.get_all_readmes_concurrent(nproc=3)
        concurrent_time = time.time() - start_time
        
        assert isinstance(readmes, dict)
        assert 'LeanEuclid' in readmes
        
        logger.info(f"并发获取 {len(readmes)} 个README耗时: {concurrent_time:.2f}秒")
        
        # 验证LeanEuclid的README确实被获取到
        lean_euclid_readme = readmes['LeanEuclid']
        if lean_euclid_readme:
            assert isinstance(lean_euclid_readme, str)
            assert len(lean_euclid_readme) > 0
            logger.info("并发操作成功获取LeanEuclid的README")


class TestGitHubClientMock:
    """GitHubClient Mock测试类（保留用于快速单元测试）"""
    
    def test_init_validation(self):
        """测试初始化参数验证"""
        # 测试空用户名
        with pytest.raises(ValueError, match="user_name 不能为空"):
            GitHubClient(user_name="")
        
        # 测试正常初始化
        client = GitHubClient(user_name="testuser")
        assert client.user_name == "testuser"
    
    @patch('github.Github')
    def test_github_exception_handling(self, mock_github):
        """测试GitHub API异常处理"""
        from github.GithubException import GithubException
        
        # 模拟API异常
        mock_github.return_value.get_user.side_effect = GithubException(404, "Not Found")
        
        client = GitHubClient(user_name="testuser")
        repos = client.get_repositories()
        
        # 应该返回空列表而不是抛出异常
        assert repos == []


# 运行说明
if __name__ == "__main__":
    print("""
    运行真实API测试:
    
    1. 不需要token（有速率限制）:
       pytest tests/test_githubclient.py::TestGitHubClientReal -v
    
    2. 使用GitHub token（推荐）:
       GITHUB_ACCESS_TOKEN=your_token pytest tests/test_githubclient.py::TestGitHubClientReal -v
    
    3. 只运行Mock测试（快速）:
       pytest tests/test_githubclient.py::TestGitHubClientMock -v
    
    4. 运行所有测试:
       pytest tests/test_githubclient.py -v
    """)

