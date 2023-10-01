#!/usr/bin/env python

"""Tests for `chattool` package."""

from click.testing import CliRunner
import chattool, json
from chattool import cli
from chattool import Chat, Resp
import pytest


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'chattool.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output

# test for the chat class
def test_chat():
    # initialize
    chat = Chat()
    assert chat.chat_log == []
    chat = Chat([{"role": "user", "content": "hello!"}])
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    chat = Chat("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]

    # general usage
    chat = Chat()
    chat.user("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    chat.assistant("Hello, how can I assist you today?")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}
    ]
    chat.system("I am a system message")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"},
        {"role": "system", "content": "I am a system message"}
    ]
    chat.clear()
    assert chat.chat_log == []

    # user/assistant/system
    chat.user("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    chat.assistant("Hello, how can I assist you today?")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}
    ]
    chat.system("I am a system message")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"},
        {"role": "system", "content": "I am a system message"}
    ]
    # get index
    assert all(chat[i]== chat.chat_log[i] for i in range(len(chat)))
    # pop/copy/clear
    chat.pop()
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}
    ]
    chat.pop()
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"}
    ]
    chat.pop()
    assert chat.chat_log == []
    chat.user("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    chat.assistant("Hello, how can I assist you today?")
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    chat2 = chat.copy()
    assert chat2.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    chat2.user("hello!")
    assert chat2.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"},
        {"role": "user", "content": "hello!"}]
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    chat2.pop()
    assert chat2.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    chat2.clear()
    assert chat2.chat_log == []
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    
    # save json
    chat.save("test.log", mode="w")
    with open("test.log", "r") as f:
        data = json.loads(f.read())
    chat2 = Chat(data)
    assert chat2.chat_log == chat.chat_log

    # print log
    chat.print_log()
    chat.print_log(sep='\n')
    print(chat)
    repr(chat)

    # len
    assert len(chat) == 2
    chat.pop()
    assert len(chat) == 1

def test_chat_broken():
    # invalid initialization
    with pytest.raises(ValueError):
        Chat(123)
    # invalid functions
    with pytest.raises(AssertionError):
        Chat(functions={})
    
# test for long chatting
response = {
    "id":"chatcmpl-6wXDUIbYzNkmqSF9UnjPuKLP1hHls",
    "object":"chat.completion",
    "created":1679408728,
    "model":"gpt-3.5-turbo-0301",
    "usage":{
        "prompt_tokens":8,
        "completion_tokens":10,
        "total_tokens":18
    },
    "choices":[
        {
            "message":{
                "role":"assistant",
                "content":"Hello, how can I assist you today?"
            },
            "finish_reason":"stop",
            "index":0
        }
    ]
}

err_api_key_resp = {
    "error": {
        "message": "Incorrect API key provided: sk-132. You can find your API key at https://platform.openai.com/account/api-keys.",
        "type": "invalid_request_error",
        "param": None,
        "code": "invalid_api_key"
    }
}

def test_long_talk():
    resp = Resp(response=response)
    msg = "hello!"
    chat = Chat(msg)
    chat.assistant(resp.content)
    assert chat.chat_log == [
        {"role": "user", "content": "hello!"},
        {"role": "assistant", "content": "Hello, how can I assist you today?"}]
    
def test_with_template():
    chat = Chat("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]
    chattool.default_prompt = lambda msg: [
        {"role": "system", "content": "I am a system message"},
        {"role": "user", "content": msg}]
    chat = Chat("hello!")
    assert chat.chat_log == [
        {"role": "system", "content": "I am a system message"},
        {"role": "user", "content": "hello!"}]
    chattool.default_prompt = None
    chat = Chat("hello!")
    assert chat.chat_log == [{"role": "user", "content": "hello!"}]

def test_error_message():
    resp = Resp(response=err_api_key_resp)
    assert resp.error_message == "Incorrect API key provided: sk-132. You can find your API key at https://platform.openai.com/account/api-keys."
    assert resp.error_type == "invalid_request_error"
    assert resp.error_param == None
    assert resp.error_code == "invalid_api_key"
    assert resp.is_valid() == False


def test_usage():
    resp = Resp(response=response)
    assert resp.total_tokens == 18
    assert resp.prompt_tokens == 8
    assert resp.completion_tokens == 10
    print(resp.cost())

def test_content():
    resp = Resp(response=response)
    assert resp.content == "Hello, how can I assist you today?"

def test_valid():
    resp = Resp(response=response)
    assert resp.id == "chatcmpl-6wXDUIbYzNkmqSF9UnjPuKLP1hHls"
    assert resp.model == "gpt-3.5-turbo-0301"
    assert resp.created == 1679408728
    assert resp.is_valid() == True

def test_show():
    resp = Resp(response=response)
    assert str(resp) == resp.content
    assert repr(resp) == "<Resp with finished reason: stop>"
  