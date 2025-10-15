"""Smoke tests for chattool package - basic functionality without external API calls"""

import pytest
from chattool import Chat
from chattool.core.config import OpenAIConfig, AzureOpenAIConfig


def test_import_chattool():
    """Test that chattool can be imported successfully"""
    import chattool
    assert hasattr(chattool, 'Chat')
    assert hasattr(chattool, 'OpenAIClient')
    assert hasattr(chattool, 'AzureOpenAIClient')


def test_chat_creation():
    """Test Chat object creation with different configs"""
    # Test with default OpenAI config
    chat = Chat()
    assert chat is not None
    assert hasattr(chat, 'user')
    assert hasattr(chat, 'assistant')
    assert hasattr(chat, 'system')
    
    # Test with explicit OpenAI config
    openai_config = OpenAIConfig()
    chat_openai = Chat(config=openai_config)
    assert chat_openai is not None
    
    # Test with Azure config
    azure_config = AzureOpenAIConfig()
    chat_azure = Chat(config=azure_config)
    assert chat_azure is not None


def test_chat_message_management():
    """Test basic message management functionality"""
    chat = Chat()
    
    # Test adding messages
    chat.user("Hello")
    assert len(chat) == 1
    assert chat[0]['role'] == 'user'
    assert chat[0]['content'] == 'Hello'
    
    chat.assistant("Hi there!")
    assert len(chat) == 2
    assert chat[1]['role'] == 'assistant'
    
    chat.system("You are a helpful assistant")
    assert len(chat) == 3
    assert chat[2]['role'] == 'system'
    
    # Test clear
    chat.clear()
    assert len(chat) == 0


def test_chat_copy():
    """Test chat copying functionality"""
    chat = Chat()
    chat.user("Test message")
    
    chat_copy = chat.copy()
    assert len(chat_copy) == 1
    assert chat_copy[0]['content'] == "Test message"
    
    # Ensure they are independent
    chat.user("Another message")
    assert len(chat) == 2
    assert len(chat_copy) == 1


def test_chat_pop():
    """Test message removal functionality"""
    chat = Chat()
    chat.user("First")
    chat.user("Second")
    chat.user("Third")
    
    # Pop last message
    popped = chat.pop()
    assert popped['content'] == "Third"
    assert len(chat) == 2
    
    # Pop specific index
    popped = chat.pop(0)
    assert popped['content'] == "First"
    assert len(chat) == 1
    assert chat[0]['content'] == "Second"


def test_config_creation():
    """Test configuration object creation"""
    # OpenAI config
    openai_config = OpenAIConfig()
    assert openai_config.model is not None
    assert hasattr(openai_config, 'api_key')
    assert hasattr(openai_config, 'api_base')
    
    # Azure config
    azure_config = AzureOpenAIConfig()
    assert azure_config.model is not None
    assert hasattr(azure_config, 'api_key')
    assert hasattr(azure_config, 'api_base')


def test_chat_properties():
    """Test chat object properties"""
    chat = Chat()
    
    # Test empty chat properties
    assert chat.last_message is None
    assert chat.last_response is None
    
    # Add a message and test
    chat.user("Test message")
    assert chat.last_message == "Test message"


def test_chat_repr():
    """Test chat string representation"""
    chat = Chat()
    repr_str = repr(chat)
    assert "Chat" in repr_str
    assert "messages" in repr_str
    
    str_str = str(chat)
    assert str_str == repr_str


if __name__ == "__main__":
    pytest.main([__file__])