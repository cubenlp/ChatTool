import os
import platformdirs
from pathlib import Path
import dotenv

CHATTOOL_CACHE_DIR = Path(platformdirs.user_cache_dir('chattool'))

CHATTOOL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

CHATTOOL_ENV_FILE = CHATTOOL_CACHE_DIR / '.env'

# setup environment variables
# environment > CACHE_DIR/.env file > default values
_env_values = dotenv.dotenv_values(CHATTOOL_ENV_FILE)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or _env_values.get('OPENAI_API_KEY')
OPENAI_API_MODEL = os.getenv('OPENAI_API_MODEL') or _env_values.get('OPENAI_API_MODEL') or 'gpt-3.5-turbo'
OPENAI_API_BASE_URL = os.getenv('OPENAI_API_BASE_URL') or _env_values.get('OPENAI_API_BASE_URL')
_api_base = os.getenv('OPENAI_API_BASE')
if _api_base is None:
    _api_base = _env_values.get('OPENAI_API_BASE')
    if _api_base is None and OPENAI_API_BASE_URL:
        _api_base = OPENAI_API_BASE_URL.rstrip('/') + '/v1'
OPENAI_API_BASE = _api_base or 'https://api.openai.com/v1'
