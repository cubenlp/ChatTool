"""Unit test package for chattool."""
from batch_executor import setup_logger
from chattool.const import CHATTOOL_REPO_DIR

test_dir = CHATTOOL_REPO_DIR / 'tests' / 'testfiles'
test_dir.mkdir(parents=True, exist_ok=True)

logger = setup_logger('test', log_level="DEBUG")