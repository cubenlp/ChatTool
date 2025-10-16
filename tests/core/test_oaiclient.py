import pytest
import json
from unittest.mock import Mock, patch
from typing import Dict, Any
from chattool.core.config import OpenAIConfig
from chattool.core.request import OpenAIClient

@pytest.fixture
def mock_response_data():
    """模拟的 OpenAI API 响应数据"""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you today?"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 9,
            "total_tokens": 19
        }
    }

class TestOpenAIConfig:
    """测试 OpenAI 配置类"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = OpenAIConfig()
        assert config.api_base
        assert config.model
        # assert 'Authorization' in config.headers
    
    def test_config_with_custom_values(self):
        """测试自定义配置值"""
        config = OpenAIConfig(
            model="gpt-4",
            temperature=0.5,
            max_tokens=1000
        )
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
    
    def test_config_get_method(self):
        """测试配置的 get 方法"""
        config = OpenAIConfig(temperature=0.7)
        assert config.get('temperature') == 0.7
        assert config.get('nonexistent') is None
        assert config.get('nonexistent', 'default') == 'default'


class TestOpenAIClient:
    """测试 OpenAI 客户端类"""
    
    def test_client_initialization(self, oai_config: OpenAIConfig):
        """测试客户端初始化"""
        client = OpenAIClient(oai_config)
        assert client.config == oai_config
        assert client._sync_client is None
        assert client._async_client is None
    
    def test_client_with_default_config(self):
        """测试使用默认配置初始化客户端"""
        client = OpenAIClient()
        assert isinstance(client.config, OpenAIConfig)
    
    def test_build_chat_data_basic(self, oai_client: OpenAIClient):
        """测试基础聊天数据构建"""
        messages = [{"role": "user", "content": "Hello"}]
        data = oai_client._build_chat_data(messages)
        
        assert data["messages"] == messages
        assert "model" in data  # 应该从 config 中获取
    
    def test_build_chat_data_with_kwargs(self, oai_client: OpenAIClient):
        """测试带 kwargs 的聊天数据构建"""
        messages = [{"role": "user", "content": "Hello"}]
        data = oai_client._build_chat_data(
            messages, 
            temperature=0.5, 
            max_tokens=100
        )
        
        assert data["messages"] == messages
        assert data["temperature"] == 0.5
        assert data["max_tokens"] == 100
    
    def test_build_chat_data_excludes_config_attrs(self, oai_client: OpenAIClient):
        """测试构建数据时排除配置专用属性"""
        messages = [{"role": "user", "content": "Hello"}]
        data = oai_client._build_chat_data(messages)
        
        # 这些属性不应该出现在 API 请求数据中
        for attr in oai_client._config_only_attrs:
            assert attr not in data
    
    def test_get_param_value_priority(self, oai_client: OpenAIClient):
        """测试参数值优先级"""
        # kwargs 优先于 config
        kwargs = {"temperature": 0.8}
        value = oai_client._get_param_value("temperature", kwargs)
        assert value == 0.8
        
        # 没有 kwargs 时使用 config
        value = oai_client._get_param_value("model", {})
        assert value == oai_client.config.model
        
        # 都没有时返回 None
        value = oai_client._get_param_value("nonexistent", {})
        assert value is None
    
    @patch('chattool.core.request.OpenAIClient.post')
    def test_chat_completion_sync(self, mock_post, oai_client: OpenAIClient, mock_response_data):
        """测试同步聊天完成"""
        # 设置 mock
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        result = oai_client.chat_completion(messages)
        
        # 验证调用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/chat/completions"
        assert "data" in call_args[1]
        assert call_args[1]["data"]["messages"] == messages
        
        # 验证返回值
        assert result == mock_response_data
    
    @patch('chattool.core.request.OpenAIClient.async_post')
    @pytest.mark.asyncio
    async def test_chat_completion_async(self, mock_async_post, oai_client: OpenAIClient, mock_response_data):
        """测试异步聊天完成"""
        # 设置 mock
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_async_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        result = await oai_client.chat_completion_async(messages)
        
        # 验证调用
        mock_async_post.assert_called_once()
        call_args = mock_async_post.call_args
        assert call_args[0][0] == "/chat/completions"
        assert "data" in call_args[1]
        assert call_args[1]["data"]["messages"] == messages
        
        # 验证返回值
        assert result == mock_response_data
    
    def test_chat_completion_parameter_override(self, oai_client: OpenAIClient):
        """测试参数覆盖功能"""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch.object(oai_client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_post.return_value = mock_response
            
            # 调用时覆盖配置参数
            oai_client.chat_completion(
                messages, 
                model="gpt-4",
                temperature=0.2,
                custom_param="test"
            )
            
            # 验证数据中包含覆盖的参数
            call_data = mock_post.call_args[1]["data"]
            assert call_data["model"] == "gpt-4"
            assert call_data["temperature"] == 0.2
            assert call_data["custom_param"] == "test"
    
    @patch('chattool.core.request.OpenAIClient.post')
    def test_embeddings(self, mock_post, oai_client: OpenAIClient):
        """测试嵌入 API"""
        mock_response_data = {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": [0.1, 0.2, 0.3],
                    "index": 0
                }
            ],
            "model": "text-embedding-ada-002",
            "usage": {"prompt_tokens": 5, "total_tokens": 5}
        }
        
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_post.return_value = mock_response
        
        result = oai_client.embeddings("test text")
        
        # 验证调用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/embeddings"
        assert call_args[1]["data"]["input"] == "test text"
        
        # 验证返回值
        assert result == mock_response_data
    
    @patch('chattool.core.request.OpenAIClient.async_post')
    @pytest.mark.asyncio
    async def test_embeddings_async(self, mock_async_post, oai_client: OpenAIClient):
        """测试异步嵌入 API"""
        mock_response_data = {
            "object": "list",
            "data": [{"embedding": [0.1, 0.2]}],
            "model": "text-embedding-ada-002"
        }
        
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_async_post.return_value = mock_response
        
        result = await oai_client.embeddings_async(["text1", "text2"])
        
        # 验证调用
        mock_async_post.assert_called_once()
        call_args = mock_async_post.call_args
        assert call_args[0][0] == "/embeddings"
        assert call_args[1]["data"]["input"] == ["text1", "text2"]
        
        # 验证返回值
        assert result == mock_response_data


class TestParameterHandling:
    """测试参数处理逻辑"""
    
    def test_none_values_excluded(self, oai_client: OpenAIClient):
        """测试 None 值被排除"""
        messages = [{"role": "user", "content": "Hello"}]
        data = oai_client._build_chat_data(
            messages,
            temperature=None,
            max_tokens=100,
            top_p=None
        )
        
        assert "temperature" not in data
        assert "top_p" not in data
        assert data["max_tokens"] == 100
    
    def test_config_fallback(self, oai_client: OpenAIClient):
        """测试配置回退机制"""
        # 设置一些配置值
        oai_client.config.temperature = 0.7
        oai_client.config.custom_param = "config_value"
        
        messages = [{"role": "user", "content": "Hello"}]
        data = oai_client._build_chat_data(messages)
        
        # 应该使用配置中的值
        assert data["temperature"] == 0.7
        assert data["custom_param"] == "config_value"
    
    def test_kwargs_override_config(self, oai_client: OpenAIClient):
        """测试 kwargs 覆盖配置"""
        # 设置配置值
        oai_client.config.temperature = 0.7
        
        messages = [{"role": "user", "content": "Hello"}]
        data = oai_client._build_chat_data(
            messages,
            temperature=0.2  # 覆盖配置
        )
        
        # 应该使用 kwargs 中的值
        assert data["temperature"] == 0.2
    
    def test_unknown_parameters_included(self, oai_client: OpenAIClient):
        """测试未知参数也会被包含"""
        messages = [{"role": "user", "content": "Hello"}]
        data = oai_client._build_chat_data(
            messages,
            future_param="new_feature",
            another_param={"complex": "value"}
        )
        
        assert data["future_param"] == "new_feature"
        assert data["another_param"] == {"complex": "value"}
