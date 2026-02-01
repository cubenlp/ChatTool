"""Unit test package for chattool."""
from chattool.utils import setup_logger
from chattool.const import CHATTOOL_REPO_DIR
from dotenv import load_dotenv
load_dotenv(CHATTOOL_REPO_DIR / '.env')

test_dir = CHATTOOL_REPO_DIR / 'tests' / 'testfiles'
test_dir.mkdir(parents=True, exist_ok=True)

logger = setup_logger('test', log_level="DEBUG")