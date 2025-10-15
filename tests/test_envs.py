# Test for api_base, base_url, chat_url

import chattool
from chattool import Chat, save_envs, load_envs

def test_model_api_key():
    import os
    # 保存原始环境变量
    original_api_key = os.environ.get('OPENAI_API_KEY')
    original_model = os.environ.get('OPENAI_API_MODEL')
    
    # 清除环境变量
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
    if 'OPENAI_API_MODEL' in os.environ:
        del os.environ['OPENAI_API_MODEL']
    
    from chattool.core.config import OpenAIConfig
    config = OpenAIConfig()
    chat = Chat(config=config)
    assert chat.config.api_key == ''
    assert chat.config.model == 'gpt-3.5-turbo'  # 默认模型
    
    config = OpenAIConfig(api_key="sk-123", model="gpt-3.5-turbo")
    chat = Chat(config=config)
    assert chat.config.api_key == "sk-123"
    assert chat.config.model == "gpt-3.5-turbo"
    
    # 恢复环境变量
    if original_api_key:
        os.environ['OPENAI_API_KEY'] = original_api_key
    if original_model:
        os.environ['OPENAI_API_MODEL'] = original_model

def test_apibase():
    import os
    from chattool.core.config import OpenAIConfig
    
    # 保存原始环境变量
    original_api_base = os.environ.get('OPENAI_API_BASE')
    
    # 测试 api_base 设置
    config = OpenAIConfig(api_base="https://api.pytest1.com/v1")
    chat = Chat(config=config)
    assert chat.config.api_base == "https://api.pytest1.com/v1"

    # 测试默认 api_base（清除环境变量）
    if 'OPENAI_API_BASE' in os.environ:
        del os.environ['OPENAI_API_BASE']
    config = OpenAIConfig()
    chat = Chat(config=config)
    assert chat.config.api_base == "https://api.openai.com/v1"
    
    # 测试自定义 api_base
    config = OpenAIConfig(api_base="https://api.pytest2.com/v1")
    chat = Chat(config=config)
    assert chat.config.api_base == "https://api.pytest2.com/v1"
    
    # 恢复环境变量
    if original_api_base:
        os.environ['OPENAI_API_BASE'] = original_api_base

def test_env_file(testpath):
    save_envs(testpath + "chattool.env")
    with open(testpath + "test.env", "w") as f:
        f.write("OPENAI_API_KEY=sk-132\n")
        f.write("OPENAI_API_BASE_URL=https://api.example.com\n")
        f.write("OPENAI_API_MODEL=gpt-3.5-turbo-0301\n")
    load_envs(testpath + "test.env")
    assert chattool.api_key == "sk-132"
    assert chattool.base_url == "https://api.example.com"
    assert chattool.model == "gpt-3.5-turbo-0301"
    # reset the environment variables
    load_envs(testpath + "chattool.env")