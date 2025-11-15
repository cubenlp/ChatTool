import pytest
from unittest.mock import Mock, patch, AsyncMock
from chattool.core import Chat


@pytest.fixture
def mock_response_data():
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 9, "total_tokens": 19},
    }


def test_chat_initialization_defaults():
    chat = Chat()
    assert chat.api_key is not None
    assert chat.model is not None
    assert chat.config.api_base is not None


@patch('chattool.core.chattype.Chat.post')
def test_chat_completion_sync(mock_post, mock_response_data):
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_post.return_value = mock_response

    chat = Chat(api_key='test-key', api_base='http://127.0.0.1:8000', model='gpt-4')
    messages = [{"role": "user", "content": "Hello"}]
    result = chat.chat_completion(messages)

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "/chat/completions"
    assert "data" in call_args[1]
    assert call_args[1]["data"]["messages"] == messages
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"
    assert result == mock_response_data


@patch('chattool.core.chattype.Chat.async_post')
@pytest.mark.asyncio
async def test_async_chat_completion(mock_async_post, mock_response_data):
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_async_post.return_value = mock_response

    chat = Chat(api_key='test-key', api_base='http://127.0.0.1:8000', model='gpt-4')
    messages = [{"role": "user", "content": "Hello"}]
    result = await chat.async_chat_completion(messages)

    mock_async_post.assert_called_once()
    call_args = mock_async_post.call_args
    assert call_args[0][0] == "/chat/completions"
    assert "data" in call_args[1]
    assert call_args[1]["data"]["messages"] == messages
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"
    assert result == mock_response_data


def test_chat_completion_parameter_override():
    chat = Chat(api_key='test-key', api_base='http://127.0.0.1:8000', model='gpt-4')
    messages = [{"role": "user", "content": "Hello"}]

    with patch.object(chat, 'post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        chat.chat_completion(messages, model="gpt-4", temperature=0.2, custom_param="test")

        call_data = mock_post.call_args[1]["data"]
        assert call_data["model"] == "gpt-4"
        assert call_data["temperature"] == 0.2
        assert call_data["custom_param"] == "test"


def test_chat_merges_default_kwargs_into_data():
    chat = Chat(api_key='test-key', api_base='http://127.0.0.1:8000', model='gpt-4', default_role='system')
    messages = [{"role": "user", "content": "Hello"}]

    with patch.object(chat, 'post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        chat.chat_completion(messages)
        call_data = mock_post.call_args[1]["data"]
        assert call_data["messages"] == messages
        assert call_data["default_role"] == "system"


def test_message_helpers_user_assistant_system():
    chat = Chat()
    chat.user('hi').assistant('hello').system('rule')
    assert len(chat) == 3
    assert chat[0]['role'] == 'user'
    assert chat[1]['role'] == 'assistant'
    assert chat[2]['role'] == 'system'


@pytest.mark.asyncio
async def test_async_get_response_updates_history():
    chat = Chat(api_key='test-key', api_base='http://127.0.0.1:8000', model='gpt-4')
    chat.user('hi')
    fake = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1,
        "model": "gpt-4",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "hello"},
            "finish_reason": "stop"
        }]
    }
    with patch.object(chat, 'async_chat_completion', new=AsyncMock(return_value=fake)):
        response = await chat.async_get_response(update_history=True)
        assert response is not None
        assert len(chat) == 2  # user + assistant
        assert chat[-1]['role'] == 'assistant'