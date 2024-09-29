# Test for api_base, base_url, chat_url

import chattool
from chattool import Chat, save_envs, load_envs

def test_model_api_key():
    api_key, model = chattool.api_key, chattool.model
    chattool.api_key, chattool.model = None, None
    chat = Chat()
    assert chat.api_key == ''
    assert chat.model == ''
    chattool.api_key, chattool.model = api_key, model
    chat = Chat(api_key="sk-123", model="gpt-3.5-turbo")
    assert chat.api_key == "sk-123"
    assert chat.model == "gpt-3.5-turbo"

def test_apibase():
    api_base, base_url = chattool.api_base, chattool.base_url
    chattool.api_base, chattool.base_url = None, None
    # chat_url > api_base > base_url > chattool.api_base > chattool.base_url
    # chat_url > api_base
    chat = Chat(chat_url="https://api.pytest1.com/v1/chat/completions", api_base="https://api.pytest2.com/v1")
    assert chat.chat_url == "https://api.pytest1.com/v1/chat/completions"

    # api_base > base_url
    chat = Chat(api_base="https://api.pytest2.com/v1", base_url="https://api.pytest3.com")
    assert chat.chat_url == "https://api.pytest2.com/v1/chat/completions"

    # base_url > chattool.api_base
    chattool.api_base = "https://api.pytest2.com/v1"
    chat = Chat(base_url="https://api.pytest3.com")
    assert chat.chat_url == "https://api.pytest3.com/v1/chat/completions"

    # chattool.api_base > chattool.base_url
    chattool.base_url = "https://api.pytest4.com"
    chat = Chat()
    assert chat.chat_url == "https://api.pytest2.com/v1/chat/completions"
    
    # base_url > chattool.api_base, chattool.base_url
    chat = Chat(base_url="https://api.pytest3.com")
    assert chat.chat_url == "https://api.pytest3.com/v1/chat/completions"

    chattool.api_base, chattool.base_url = api_base, base_url

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