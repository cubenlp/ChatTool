"""Unit test package for chattool."""

from chattool import Chat, debug_log
import os

if not os.path.exists('tests'):
    os.mkdir('tests')
if not os.path.exists('tests/testfiles'):
    os.mkdir('tests/testfiles')

def test_simple():
    # set api_key in the environment variable
    chat = Chat()
    chat.user("Hello!")
    chat.getresponse()
    debug_log()
    assert chat.chat_log[0] == {"role": "user", "content": "Hello!"}
    assert len(chat.chat_log) == 2
    