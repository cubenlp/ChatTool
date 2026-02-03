import pytest
import os
from chattool import ClaudeChat
from chattool.utils.config import ClaudeConfig
from chattool.utils import load_envs

@pytest.fixture(scope="module", autouse=True)
def load_config():
    """Load configuration from .env file"""
    env_path = os.path.expanduser("~/.config/chattool/.env")
    if os.path.exists(env_path):
        load_envs(env_path)
    else:
        load_envs() # Try default locations

@pytest.fixture
def claude_chat():
    # Initialize ClaudeChat with real configuration
    # Force model to gpt-3.5-turbo as it is the only one available on the provided endpoint
    chat = ClaudeChat(model="gpt-3.5-turbo")
    
    # Check if we have valid credentials
    if not chat.api_key or "dummy" in chat.api_key:
        pytest.skip("Skipping real API tests: CLAUDE_API_KEY not set or invalid")
        
    yield chat

def test_init_uses_env_defaults(claude_chat):
    """Test that initialization uses environment variables"""
    assert claude_chat.api_key is not None
    assert claude_chat.model is not None
    assert claude_chat.config.api_base is not None

def test_basic_sync_flow(claude_chat):
    """Test basic synchronous chat flow"""
    claude_chat.system("You are a helpful assistant.")
    claude_chat.user("Hello")
    resp = claude_chat.get_response(update_history=True)

    assert resp.is_valid()
    assert isinstance(resp.content, str)
    assert len(resp.content) > 0
    assert claude_chat.chat_log[-1]["role"] == "assistant"
    assert claude_chat.last_response == resp

@pytest.mark.asyncio
async def test_async_ask(claude_chat):
    """Test async ask convenience method"""
    claude_chat.clear()
    answer = await claude_chat.async_ask("Hi there")
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert claude_chat.chat_log[-1]["role"] == "assistant"

@pytest.mark.asyncio
async def test_async_get_response(claude_chat):
    """Test async get_response method"""
    claude_chat.clear()
    claude_chat.user("Test async")
    resp = await claude_chat.async_get_response(update_history=True)

    assert resp.is_valid()
    assert resp.message is not None
    assert isinstance(resp.content, str)
    assert claude_chat.chat_log[-1]["role"] == "assistant"

def test_message_helpers(claude_chat):
    """Test message helper methods"""
    claude_chat.clear()
    claude_chat.system("Sys").user("User").assistant("Asst")
    assert [m["role"] for m in claude_chat.chat_log] == ["system", "user", "assistant"]
    
    popped = claude_chat.pop()
    assert popped["role"] == "assistant"
    assert len(claude_chat.chat_log) == 2

def test_copy(claude_chat):
    """Test copy functionality"""
    claude_chat.clear()
    claude_chat.user("Original")
    c2 = claude_chat.copy()
    
    assert c2.chat_log == claude_chat.chat_log
    assert isinstance(c2, ClaudeChat)
    
    c2.user("Appended")
    assert len(c2.chat_log) == len(claude_chat.chat_log) + 1
