"""Unit test package for chatapi_toolkit."""

from chatapi_toolkit import Chat

def test_simple():
    # set api_key in the environment variable
    chat = Chat()
    chat.user("Hello!")
    chat.getresponse()
    chat.print_log()
    assert chat.chat_log[0] == {"role": "user", "content": "Hello!"}
    assert len(chat.chat_log) == 2
    