import pytest
import os
from dotenv import load_dotenv
from chattool.const import CHATTOOL_REPO_DIR
from chattool.core import HTTPClient, HTTPConfig, Chat
from chattool.tools import ZulipClient, GitHubClient

# 在收集阶段（collection phase）之前加载环境变量
def _load_envs():
    """自动加载项目根目录下的环境变量文件"""
    # 尝试加载项目根目录下的 .env 文件
    env_file = CHATTOOL_REPO_DIR / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    
    # 也尝试加载具体的环境文件（为了兼容旧的测试习惯）
    aliyun_env = CHATTOOL_REPO_DIR / 'aliyun.env'
    if aliyun_env.exists():
        load_dotenv(aliyun_env)
        
    tencent_env = CHATTOOL_REPO_DIR / 'tencent.env'
    if tencent_env.exists():
        load_dotenv(tencent_env)

_load_envs()

TEST_PATH = 'tests/testfiles/'

@pytest.fixture
def chat():
    c = Chat()
    c.clear()
    return c

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