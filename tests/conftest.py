import pytest
import asyncio
from chattool.core import HTTPClient, Config
from chattool.fastobj.basic import FastAPIManager
from chattool.fastobj.capture import app
from chattool.tools import ZulipClient
import time

TEST_PATH = 'tests/testfiles/'

@pytest.fixture(scope="session")
def testpath():
    return TEST_PATH

# @pytest.fixture(scope="session", autouse=True)
# def fastapi_server():
#     """在整个测试会话期间启动 FastAPI 服务"""
#     manager = FastAPIManager(app, port=8000, reload=False)
#     manager.start()
    
#     # 等待服务启动
#     time.sleep(1)
    
#     yield manager  # 提供给测试使用
    
#     # 测试结束后清理
#     manager.stop()

# @pytest.fixture(scope="session")
# def server_url():
#     """提供服务器 URL"""
#     return "http://127.0.0.1:8000"

# @pytest.fixture(scope="session")
# def config(server_url):
#     return Config(api_base=server_url)

# @pytest.fixture
# def http_client(config):
#     """同步HTTP客户端"""
#     return HTTPClient(config)

@pytest.fixture
def zulip_client():
    """Zulip 客户端"""
    zulip_client = ZulipClient()
    return zulip_client