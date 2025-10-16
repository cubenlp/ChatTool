import pytest
import asyncio
from chattool.core import HTTPClient, Config, OpenAIConfig, OpenAIClient, AzureOpenAIConfig, AzureOpenAIClient
from chattool.fastobj.basic import FastAPIManager
from chattool.fastobj.capture import app
from chattool.tools import ZulipClient, GitHubClient
import time

TEST_PATH = 'tests/testfiles/'

@pytest.fixture
def testpath():
    return TEST_PATH

@pytest.fixture
def oai_config():
    """OpenAI 配置"""
    return OpenAIConfig()

@pytest.fixture
def oai_client(oai_config):
    """OpenAI 客户端"""
    return OpenAIClient(oai_config)

@pytest.fixture
def azure_config():
    """Azure OpenAI 配置 fixture"""
    return AzureOpenAIConfig(
        api_key="test-azure-key",
        api_base="https://test-resource.openai.azure.com",
        api_version="2024-02-15-preview",
        model="gpt-35-turbo"
    )

@pytest.fixture
def azure_client(azure_config):
    """Azure OpenAI 客户端 fixture"""
    return AzureOpenAIClient(azure_config)

@pytest.fixture(scope="session", autouse=True)
def fastapi_server():
    """在整个测试会话期间启动 FastAPI 服务"""
    manager = FastAPIManager(app, port=8000, reload=False)
    manager.start()
    
    # 等待服务启动
    time.sleep(1)
    
    yield manager  # 提供给测试使用
    
    # 测试结束后清理
    manager.stop()

@pytest.fixture(scope="session")
def server_url():
    """提供服务器 URL"""
    return "http://127.0.0.1:8000"

@pytest.fixture(scope="session")
def config(server_url):
    return Config(api_base=server_url)

@pytest.fixture
def http_client(config):
    """同步HTTP客户端"""
    return HTTPClient(config)

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