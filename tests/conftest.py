import pytest
from chattool.core import HTTPClient, HTTPConfig
from chattool.tools import ZulipClient, GitHubClient

TEST_PATH = 'tests/testfiles/'

@pytest.fixture
def testpath():
    return TEST_PATH

@pytest.fixture(scope="session")
def server_url():
    """提供服务器 URL"""
    return "http://127.0.0.1:8000"

@pytest.fixture(scope="session")
def config(server_url):
    return HTTPConfig(api_base=server_url)

@pytest.fixture
def http_client(config):
    """同步HTTP客户端"""
    return HTTPClient(api_base=config.api_base)

@pytest.fixture
def zulip_client():
    """Zulip 客户端"""
    zulip_client = ZulipClient()
    return zulip_client

@pytest.fixture
def github_client():
    """GitHub 客户端"""
    # 使用测试用户名，token从环境变量获取
    github_client = GitHubClient(user_name="octocat")  # GitHub的官方测试用户
    return github_client

@pytest.fixture
def github_client_with_token():
    """带token的GitHub客户端（用于需要认证的测试）"""
    import os
    token = os.getenv('GITHUB_ACCESS_TOKEN')
    if not token:
        pytest.skip("需要GITHUB_ACCESS_TOKEN环境变量")
    github_client = GitHubClient(user_name="octocat", token=token)
    return github_client