from chatenv.configs import OpenAIConfig as SharedOpenAIConfig
from chattool.config import OpenAIConfig


def test_openai_config_reexports_chatenv_shared_fields_and_keeps_chattool_test():
    assert OpenAIConfig is SharedOpenAIConfig
    assert OpenAIConfig.OPENAI_API_KEY is SharedOpenAIConfig.OPENAI_API_KEY
    assert OpenAIConfig.OPENAI_IMAGE_MODEL is SharedOpenAIConfig.OPENAI_IMAGE_MODEL
    assert callable(OpenAIConfig.test)
    assert callable(OpenAIConfig._test_responses_api)


def test_chattool_does_not_reexport_feishu_or_image_provider_configs():
    import chattool.config as config

    removed = {
        "FeishuConfig",
        "TongyiConfig",
        "HuggingFaceConfig",
        "PollinationsConfig",
        "LiblibConfig",
        "SiliconFlowConfig",
    }
    for name in removed:
        assert name not in config.__all__
        assert not hasattr(config, name)
