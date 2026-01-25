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

# OpenAI
OPENAI_API_KEY = _env_values.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
OPENAI_API_MODEL = _env_values.get('OPENAI_API_MODEL') or os.getenv('OPENAI_API_MODEL')  or 'gpt-3.5-turbo'
OPENAI_API_BASE_URL = _env_values.get('OPENAI_API_BASE_URL') or os.getenv('OPENAI_API_BASE_URL')
_api_base = _env_values.get('OPENAI_API_BASE') or os.getenv('OPENAI_API_BASE')
if _api_base is None and OPENAI_API_BASE_URL:
    _api_base = OPENAI_API_BASE_URL.rstrip('/') + '/v1'
OPENAI_API_BASE = _api_base or 'https://api.openai.com/v1'

# Azure OpenAI
AZURE_OPENAI_API_KEY = _env_values.get('AZURE_OPENAI_API_KEY') or os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = _env_values.get('AZURE_OPENAI_ENDPOINT') or os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = _env_values.get('AZURE_OPENAI_API_VERSION') or os.getenv('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_API_MODEL = _env_values.get('AZURE_OPENAI_API_MODEL') or os.getenv('AZURE_OPENAI_API_MODEL')

# Alibaba Cloud (Aliyun)
ALIBABA_CLOUD_ACCESS_KEY_ID = _env_values.get('ALIBABA_CLOUD_ACCESS_KEY_ID') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
ALIBABA_CLOUD_ACCESS_KEY_SECRET = _env_values.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET') or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
ALIBABA_CLOUD_REGION_ID = _env_values.get('ALIBABA_CLOUD_REGION_ID') or os.getenv('ALIBABA_CLOUD_REGION_ID') or 'cn-hangzhou'

# Tencent Cloud
TENCENT_SECRET_ID = _env_values.get('TENCENT_SECRET_ID') or os.getenv('TENCENT_SECRET_ID')
TENCENT_SECRET_KEY = _env_values.get('TENCENT_SECRET_KEY') or os.getenv('TENCENT_SECRET_KEY')
TENCENT_REGION_ID = _env_values.get('TENCENT_REGION_ID') or os.getenv('TENCENT_REGION_ID') or 'ap-guangzhou'

# Zulip
ZULIP_BOT_EMAIL = _env_values.get('ZULIP_BOT_EMAIL') or os.getenv('ZULIP_BOT_EMAIL')
ZULIP_BOT_API_KEY = _env_values.get('ZULIP_BOT_API_KEY') or os.getenv('ZULIP_BOT_API_KEY')
ZULIP_SITE = _env_values.get('ZULIP_SITE') or os.getenv('ZULIP_SITE')
