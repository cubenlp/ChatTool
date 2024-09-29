import pytest
from chattool import *

TEST_PATH = 'tests/testfiles/'

@pytest.fixture(scope="session")
def testpath():
    return TEST_PATH