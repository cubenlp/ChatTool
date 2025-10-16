import os
import platformdirs
from pathlib import Path
import dotenv

# dirs
CHATTOOL_CACHE_DIR = Path(platformdirs.user_cache_dir('chattool'))
CHATTOOL_CONFIG_DIR = Path(platformdirs.user_config_dir('chattool'))
CHATTOOL_ENV_DIR = CHATTOOL_CONFIG_DIR / 'envs'
CHATTOOL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
CHATTOOL_ENV_DIR.mkdir(parents=True, exist_ok=True)

CHATTOOL_ENV_FILE = CHATTOOL_CONFIG_DIR / '.env'
CHATTOOL_REPO_DIR = Path(__file__).parent.parent.parent

# setup environment variables
# CONFIG_DIR/.env file > environment > default values
_env_values = dotenv.dotenv_values(CHATTOOL_ENV_FILE)
OPENAI_API_KEY = _env_values.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
OPENAI_API_MODEL = _env_values.get('OPENAI_API_MODEL') or os.getenv('OPENAI_API_MODEL')  or 'gpt-3.5-turbo'
OPENAI_API_BASE_URL = _env_values.get('OPENAI_API_BASE_URL') or os.getenv('OPENAI_API_BASE_URL')
_api_base = _env_values.get('OPENAI_API_BASE') or os.getenv('OPENAI_API_BASE')
if _api_base is None and OPENAI_API_BASE_URL:
    _api_base = OPENAI_API_BASE_URL.rstrip('/') + '/v1'
OPENAI_API_BASE = _api_base or 'https://api.openai.com/v1'

# Azure OpenAI API Key
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY') or _env_values.get('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT') or _env_values.get('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION') or _env_values.get('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_API_MODEL = os.getenv('AZURE_OPENAI_API_MODEL') or _env_values.get('AZURE_OPENAI_API_MODEL')