from chatenv.configs import FeishuConfig as SharedFeishuConfig
from chatenv.configs import OpenAIConfig as SharedOpenAIConfig
from chattool.config import FeishuConfig, OpenAIConfig


def test_openai_config_reexports_chatenv_shared_fields_and_keeps_chattool_test():
    assert OpenAIConfig is SharedOpenAIConfig
    assert OpenAIConfig.OPENAI_API_KEY is SharedOpenAIConfig.OPENAI_API_KEY
    assert OpenAIConfig.OPENAI_IMAGE_MODEL is SharedOpenAIConfig.OPENAI_IMAGE_MODEL
    assert callable(OpenAIConfig.test)
    assert callable(OpenAIConfig._test_responses_api)


def test_feishu_config_reexports_chatenv_shared_fields_and_keeps_chattool_test():
    assert FeishuConfig is SharedFeishuConfig
    assert FeishuConfig.FEISHU_APP_ID is SharedFeishuConfig.FEISHU_APP_ID
    assert FeishuConfig.FEISHU_VERIFY_TOKEN is SharedFeishuConfig.FEISHU_VERIFY_TOKEN
    assert callable(FeishuConfig.test)
