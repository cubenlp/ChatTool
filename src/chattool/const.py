import platformdirs
from pathlib import Path
from chattool.utils.config import BaseEnvConfig, OpenAIConfig

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
BaseEnvConfig.load_all(CHATTOOL_ENV_FILE)

# Inject loaded values into current namespace
# This ensures backward compatibility (e.g., chattool.const.OPENAI_API_KEY)
globals().update(BaseEnvConfig.get_all_values())

# Special logic for OPENAI_API_BASE
# If OPENAI_API_BASE is not set, but OPENAI_API_BASE_URL is set, derive it.
# This logic is specific to OpenAI and hard to generalize in the declarative config,
# so we keep it here as a post-processing step.
_api_base = globals().get('OPENAI_API_BASE')
_api_base_url = globals().get('OPENAI_API_BASE_URL')

if not _api_base and _api_base_url:
    _api_base = _api_base_url.rstrip('/') + '/v1'

# Final fallback
if not _api_base:
    _api_base = 'https://api.openai.com/v1'

OPENAI_API_BASE = _api_base
# Update the config object as well, just in case
OpenAIConfig.OPENAI_API_BASE.value = _api_base
