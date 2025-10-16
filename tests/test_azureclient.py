import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import hashlib
from chattool.core.config import AzureOpenAIConfig
from chattool.core.request import AzureOpenAIClient

@pytest.fixture
def mock_azure_response_data():
    """模拟的 Azure OpenAI API 响应数据"""
    return {
        "id": "chatcmpl-azure123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-35-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello from Azure! How can I help you today?"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 11,
            "total_tokens": 23
        }
    }

class TestAzureOpenAIConfig:
    """测试 Azure OpenAI 配置类"""
    
    def test_config_initialization_with_defaults(self):
        """测试使用默认值初始化配置"""
        config = AzureOpenAIConfig()
        # assert config.api_base  # 应该有默认值或从环境变量获取
        assert 'Content-Type' in config.headers
    
    def test_config_initialization_with_custom_values(self):
        """测试自定义配置值"""
        config = AzureOpenAIConfig(
            api_key="custom-key",
            api_base="https://custom.openai.azure.com",
            api_version="2024-01-01",
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000
        )
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
    
    def test_config_api_base_construction(self):
        """测试 API 基础 URL 的构建"""
        config = AzureOpenAIConfig(
            api_key="test-key",
            api_base="https://test.openai.azure.com/",  # 带尾部斜杠
            api_version="2024-02-15-preview"
        )
        
        # 验证 URL 构建正确
        assert config.api_base.startswith("https://test.openai.azure.com")
        assert not config.api_base.endswith("//")  # 不应该有双斜杠
    
    def test_config_get_method(self):
        """测试配置的 get 方法"""
        config = AzureOpenAIConfig(temperature=0.8, max_tokens=1500)
        assert config.get('temperature') == 0.8
        assert config.get('max_tokens') == 1500
        assert config.get('nonexistent') is None
        assert config.get('nonexistent', 'default') == 'default'


class TestAzureOpenAIClient:
    """测试 Azure OpenAI 客户端类"""
    
    def test_client_initialization(self, azure_config):
        """测试客户端初始化"""
        client = AzureOpenAIClient(azure_config)
        assert client.config == azure_config
        assert isinstance(client.config, AzureOpenAIConfig)
        assert client._sync_client is None
        assert client._async_client is None
    
    def test_client_with_default_config(self):
        """测试使用默认配置初始化客户端"""
        client = AzureOpenAIClient()
        assert isinstance(client.config, AzureOpenAIConfig)
    
    def test_generate_log_id(self, azure_client):
        """测试 log ID 生成"""
        messages = [{"role": "user", "content": "Hello"}]
        log_id = azure_client._generate_log_id(messages)
        
        # 验证是 SHA256 哈希
        assert len(log_id) == 64
        assert all(c in '0123456789abcdef' for c in log_id)
        
        # 相同输入应该产生相同的 log ID
        log_id2 = azure_client._generate_log_id(messages)
        assert log_id == log_id2
        
        # 不同输入应该产生不同的 log ID
        different_messages = [{"role": "user", "content": "Hi"}]
        log_id3 = azure_client._generate_log_id(different_messages)
        assert log_id != log_id3
    
    def test_build_chat_data_excludes_azure_attrs(self, azure_client):
        """测试构建数据时排除 Azure 专用属性"""
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(messages)
        
        # 这些属性不应该出现在 API 请求数据中
        for attr in azure_client._config_only_attrs:
            assert attr not in data
        
        # 但应该包含必要的字段
        assert data["messages"] == messages
        assert "model" in data  # 应该从 config 中获取
    
    def test_parameter_priority_azure(self, azure_client):
        """测试 Azure 客户端的参数优先级"""
        # kwargs 优先于 config
        kwargs = {"temperature": 0.9, "max_tokens": 500}
        value = azure_client._get_param_value("temperature", kwargs)
        assert value == 0.9
        
        # 没有 kwargs 时使用 config
        value = azure_client._get_param_value("model", {})
        assert value == azure_client.config.model
    
    @patch('chattool.core.request.AzureOpenAIClient.post')
    def test_chat_completion_sync(self, mock_post, azure_client, mock_azure_response_data):
        """测试 Azure 同步聊天完成"""
        # 设置 mock
        mock_response = Mock()
        mock_response.json.return_value = mock_azure_response_data
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello Azure"}]
        result = azure_client.chat_completion(messages)
        
        # 验证调用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # 验证使用空字符串作为 endpoint（因为 api_base 已经是完整地址）
        assert call_args[0][0] == ""
        
        # 验证请求数据
        assert "data" in call_args[1]
        assert call_args[1]["data"]["messages"] == messages
        
        # 验证 Azure 特殊请求头
        assert "headers" in call_args[1]
        headers = call_args[1]["headers"]
        assert "X-TT-LOGID" in headers
        
        # 验证返回值
        assert result == mock_azure_response_data
    
    @patch('chattool.core.request.AzureOpenAIClient.async_post')
    @pytest.mark.asyncio
    async def test_chat_completion_async(self, mock_async_post, azure_client, mock_azure_response_data):
        """测试 Azure 异步聊天完成"""
        # 设置 mock
        mock_response = Mock()
        mock_response.json.return_value = mock_azure_response_data
        mock_async_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello Azure Async"}]
        result = await azure_client.chat_completion_async(messages)
        
        # 验证调用
        mock_async_post.assert_called_once()
        call_args = mock_async_post.call_args
        
        # 验证使用空字符串作为 endpoint
        assert call_args[0][0] == ""
        
        # 验证请求数据和头
        assert "data" in call_args[1]
        assert "headers" in call_args[1]
        assert "X-TT-LOGID" in call_args[1]["headers"]
        
        # 验证返回值
        assert result == mock_azure_response_data
    
    def test_parameter_override_azure(self, azure_client):
        """测试 Azure 客户端参数覆盖功能"""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch.object(azure_client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_post.return_value = mock_response
            
            # 调用时覆盖配置参数
            azure_client.chat_completion(
                messages,
                model="gpt-4",
                temperature=0.1,
                azure_custom_param="test"
            )
            
            # 验证数据中包含覆盖的参数
            call_data = mock_post.call_args[1]["data"]
            assert call_data["model"] == "gpt-4"
            assert call_data["temperature"] == 0.1
            assert call_data["azure_custom_param"] == "test"
    
    def test_config_only_attrs_azure(self, azure_client):
        """测试 Azure 配置专用属性列表"""
        expected_attrs = {
            'api_key', 'api_base', 'api_version',
            'headers', 'timeout', 'max_retries', 'retry_delay'
        }
        assert azure_client._config_only_attrs == expected_attrs


class TestAzureParameterHandling:
    """测试 Azure 参数处理逻辑"""
    
    def test_azure_none_values_excluded(self, azure_client):
        """测试 Azure 客户端排除 None 值"""
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(
            messages,
            temperature=None,
            max_tokens=100,
            api_version=None  # Azure 特有参数
        )
        
        assert "temperature" not in data
        assert "api_version" not in data
        assert data["max_tokens"] == 100
    
    def test_azure_config_fallback(self, azure_client):
        """测试 Azure 配置回退机制"""
        # 设置一些配置值
        azure_client.config.temperature = 0.8
        azure_client.config.azure_custom_param = "azure_value"
        
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(messages)
        
        # 应该使用配置中的值
        assert data["temperature"] == 0.8
        assert data["azure_custom_param"] == "azure_value"
        
        # 但不应该包含配置专用属性
        assert "api_version" not in data
        assert "api_key" not in data
    
    def test_azure_kwargs_override_config(self, azure_client):
        """测试 Azure 客户端 kwargs 覆盖配置"""
        # 设置配置值
        azure_client.config.temperature = 0.7
        azure_client.config.max_tokens = 1000
        
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(
            messages,
            temperature=0.2,  # 覆盖配置
            custom_azure_param="override_value"
        )
        
        # 应该使用 kwargs 中的值
        assert data["temperature"] == 0.2
        assert data["custom_azure_param"] == "override_value"
        # max_tokens 应该使用配置中的值
        assert data["max_tokens"] == 1000
    
    def test_azure_unknown_parameters_included(self, azure_client):
        """测试 Azure 客户端包含未知参数"""
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(
            messages,
            azure_future_param="new_azure_feature",
            custom_header_param={"complex": "azure_value"}
        )
        
        assert data["azure_future_param"] == "new_azure_feature"
        assert data["custom_header_param"] == {"complex": "azure_value"}


class TestAzureIntegration:
    """测试 Azure 集成功能"""
    
    def test_azure_vs_openai_client_compatibility(self, azure_client):
        """测试 Azure 客户端与 OpenAI 客户端的 API 兼容性"""
        # Azure 客户端应该有与 OpenAI 客户端相同的主要方法
        assert hasattr(azure_client, 'chat_completion')
        assert hasattr(azure_client, 'chat_completion_async')
        assert hasattr(azure_client, '_build_chat_data')
        assert hasattr(azure_client, '_get_param_value')
        # 但有 Azure 特有的方法
        assert hasattr(azure_client, '_generate_log_id')
