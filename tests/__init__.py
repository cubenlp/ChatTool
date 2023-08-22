"""Unit test package for openai_api_call."""

from openai_api_call import Chat

def test_simple():
    # set api_key in the environment variable
    chat = Chat()
    chat.user("Hello!")
    chat.getresponse()
    chat.print_log()
    assert chat.chat_log[0] == {"role": "user", "content": "Hello!"}
    assert len(chat.chat_log) == 2
    