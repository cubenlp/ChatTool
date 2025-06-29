import pytest
from chattool.core import HTTPClient, Config

TEST_PATH = 'tests/testfiles/'

@pytest.fixture(scope="session")
def testpath():
    return TEST_PATH

@pytest.fixture
def http_client():
    return HTTPClient(Config(api_base='http://localhost:8000'))

@pytest.fixture
def config():
    return Config(api_base='http://localhost:8000')