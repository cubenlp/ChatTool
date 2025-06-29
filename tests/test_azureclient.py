import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from chattool.core.config import AzureOpenAIConfig
from chattool.core.request import AzureOpenAIClient


@pytest.fixture
def mock_azure_response_data():
    """模拟的 Azure OpenAI API 响应数据"""
    return {
        "id": "chatcmpl-azure-test123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-35-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! This is from Azure OpenAI."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 8,
            "total_tokens": 20
        }
    }


@pytest.fixture
def mock_azure_stream_response_data():
    """模拟的 Azure 流式响应数据"""
    return [
        {
            "id": "chatcmpl-azure-test123",
            "object": "chat.completion.chunk",
            "created": 1677652288,
            "model": "gpt-35-turbo",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None
                }
            ]
        },
        {
            "id": "chatcmpl-azure-test123",
            "object": "chat.completion.chunk",
            "created": 1677652288,
            "model": "gpt-35-turbo",
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": "Hello"},
                    "finish_reason": None
                }
            ]
        },
        {
            "id": "chatcmpl-azure-test123",
            "object": "chat.completion.chunk",
            "created": 1677652288,
            "model": "gpt-35-turbo",
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": " from Azure!"},
                    "finish_reason": "stop"
                }
            ]
        }
    ]


class TestAzureOpenAIConfig:
    """测试 Azure OpenAI 配置类"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = AzureOpenAIConfig(
            api_key="test-key",
            api_base="https://test.openai.azure.com",
            api_version="2024-02-15-preview",
            model="gpt-35-turbo"
        )
        assert config.api_key == "test-key"
        assert config.api_base == "https://test.openai.azure.com"
        assert config.api_version == "2024-02-15-preview"
        assert config.model == "gpt-35-turbo"
        assert config.headers["Content-Type"] == "application/json"
    
    def test_config_with_custom_parameters(self):
        """测试自定义参数配置"""
        config = AzureOpenAIConfig(
            temperature=0.5,
            max_tokens=1000,
            top_p=0.9
        )
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.top_p == 0.9
    
    @patch.dict(os.environ, {
        "AZURE_OPENAI_API_KEY": "env-key",
        "AZURE_OPENAI_ENDPOINT": "https://env-resource.openai.azure.com",
        "AZURE_OPENAI_API_VERSION": "2024-03-01-preview",
        "AZURE_OPENAI_API_MODEL": "gpt-4"
    })
    def test_config_from_environment(self):
        """测试从环境变量获取配置"""
        config = AzureOpenAIConfig()
        assert config.api_key == "env-key"
        assert config.api_base == "https://env-resource.openai.azure.com"
        assert config.api_version == "2024-03-01-preview"
        assert config.model == "gpt-4"
    
    def test_get_request_url_basic(self):
        """测试基础请求 URL 构建"""
        config = AzureOpenAIConfig(
            api_base="https://test.openai.azure.com",
            api_version="2024-02-15-preview",
            api_key="test-key"
        )
        url = config.get_request_url()
        expected = "https://test.openai.azure.com?api-version=2024-02-15-preview&ak=test-key"
        assert url == expected
    
    def test_get_request_url_no_version(self):
        """测试没有 API 版本的 URL 构建"""
        config = AzureOpenAIConfig(
            api_base="https://test.openai.azure.com",
            api_key="test-key"
        )
        url = config.get_request_url()
        expected = "https://test.openai.azure.com&ak=test-key"
        assert url == expected
    
    def test_get_request_url_no_key(self):
        """测试没有 API 密钥的 URL 构建"""
        config = AzureOpenAIConfig(
            api_base="https://test.openai.azure.com",
            api_version="2024-02-15-preview"
        )
        url = config.get_request_url()
        expected = "https://test.openai.azure.com?api-version=2024-02-15-preview"
        assert url == expected
    
    def test_config_get_method(self):
        """测试配置的 get 方法"""
        config = AzureOpenAIConfig(temperature=0.7, api_version="2024-02-15-preview")
        assert config.get('temperature') == 0.7
        assert config.get('api_version') == "2024-02-15-preview"
        assert config.get('nonexistent') is None
        assert config.get('nonexistent', 'default') == 'default'


class TestAzureOpenAIClient:
    """测试 Azure OpenAI 客户端类"""
    
    def test_client_initialization(self, azure_config):
        """测试客户端初始化"""
        client = AzureOpenAIClient(azure_config)
        assert client.config == azure_config
        assert hasattr(client, '_config_only_attrs')
        assert 'api_version' in client._config_only_attrs
    
    def test_client_with_default_config(self):
        """测试使用默认配置初始化客户端"""
        client = AzureOpenAIClient()
        assert isinstance(client.config, AzureOpenAIConfig)
    
    def test_generate_log_id(self, azure_client):
        """测试 Log ID 生成"""
        messages = [{"role": "user", "content": "Hello"}]
        log_id_1 = azure_client._generate_log_id(messages)
        log_id_2 = azure_client._generate_log_id(messages)
        
        # 相同输入应该生成相同的 log ID
        assert log_id_1 == log_id_2
        assert len(log_id_1) == 64  # SHA256 输出长度
        
        # 不同输入应该生成不同的 log ID
        different_messages = [{"role": "user", "content": "Hi"}]
        log_id_3 = azure_client._generate_log_id(different_messages)
        assert log_id_1 != log_id_3
    
    def test_build_azure_headers(self, azure_client):
        """测试 Azure 请求头构建"""
        messages = [{"role": "user", "content": "Hello"}]
        headers = azure_client._build_azure_headers(messages)
        
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        assert "X-TT-LOGID" in headers
        assert len(headers["X-TT-LOGID"]) == 64
    
    def test_build_chat_data_basic(self, azure_client):
        """测试基础聊天数据构建"""
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(messages)
        
        assert data["messages"] == messages
        assert data["stream"] is False  # 默认为 False
        if azure_client.config.model:
            assert "model" in data
    
    def test_build_chat_data_with_kwargs(self, azure_client):
        """测试带 kwargs 的聊天数据构建"""
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(
            messages,
            temperature=0.5,
            max_tokens=100,
            stream=True
        )
        
        assert data["messages"] == messages
        assert data["temperature"] == 0.5
        assert data["max_tokens"] == 100
        assert data["stream"] is True
    
    def test_build_chat_data_excludes_config_attrs(self, azure_client):
        """测试构建数据时排除配置专用属性"""
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(messages)
        
        # 这些属性不应该出现在 API 请求数据中
        for attr in azure_client._config_only_attrs:
            assert attr not in data
    
    def test_get_param_value_priority(self, azure_client):
        """测试参数值优先级"""
        # kwargs 优先于 config
        kwargs = {"temperature": 0.8}
        value = azure_client._get_param_value("temperature", kwargs)
        assert value == 0.8
        
        # 没有 kwargs 时使用 config
        azure_client.config.temperature = 0.5
        value = azure_client._get_param_value("temperature", {})
        assert value == 0.5
        
        # 都没有时返回 None
        value = azure_client._get_param_value("nonexistent", {})
        assert value is None
    
    @patch('requests.post')
    def test_chat_completion_sync(self, mock_post, azure_client, mock_azure_response_data):
        """测试同步聊天完成"""
        # 设置 mock
        mock_response = Mock()
        mock_response.json.return_value = mock_azure_response_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        result = azure_client.chat_completion(messages)
        
        # 验证调用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # 验证 URL 包含 Azure 特定格式
        url = call_args[0][0]
        assert "api-version" in url
        assert "ak=" in url
        
        # 验证请求数据
        assert "json" in call_args[1]
        json_data = call_args[1]["json"]
        assert json_data["messages"] == messages
        
        # 验证请求头
        assert "headers" in call_args[1]
        headers = call_args[1]["headers"]
        assert "X-TT-LOGID" in headers
        
        # 验证返回值
        assert result == mock_azure_response_data
    
    @patch('aiohttp.ClientSession.post')
    @pytest.mark.asyncio
    async def test_chat_completion_async(self, mock_post, azure_client, mock_azure_response_data):
        """测试异步聊天完成"""
        # 设置 mock
        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_azure_response_data)
        mock_response.raise_for_status = Mock()
        
        # 设置异步上下文管理器
        mock_context = Mock()
        mock_context.__aenter__ = Mock(return_value=mock_response)
        mock_context.__aexit__ = Mock(return_value=None)
        mock_post.return_value = mock_context
        
        # 模拟 ClientSession
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = Mock()
            mock_session_instance.post.return_value = mock_context
            mock_session_instance.__aenter__ = Mock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = Mock(return_value=None)
            mock_session.return_value = mock_session_instance
            
            messages = [{"role": "user", "content": "Hello"}]
            result = await azure_client.async_chat_completion(messages)
            
            # 验证返回值
            assert result == mock_azure_response_data
    
    def test_chat_completion_parameter_override(self, azure_client):
        """测试参数覆盖功能"""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # 调用时覆盖配置参数
            azure_client.chat_completion(
                messages,
                model="gpt-4",
                temperature=0.2,
                custom_param="test"
            )
            
            # 验证数据中包含覆盖的参数
            call_args = mock_post.call_args
            json_data = call_args[1]["json"]
            assert json_data["model"] == "gpt-4"
            assert json_data["temperature"] == 0.2
            assert json_data["custom_param"] == "test"
    
    @patch('requests.post')
    def test_simple_request(self, mock_post, azure_client, mock_azure_response_data):
        """测试简化的请求方法"""
        # 设置 mock
        mock_response = Mock()
        mock_response.json.return_value = mock_azure_response_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # 测试字符串输入
        result = azure_client.simple_request("Hello, how are you?")
        expected_content = mock_azure_response_data['choices'][0]['message']['content']
        assert result == expected_content
        
        # 验证自动转换为消息格式
        call_args = mock_post.call_args
        json_data = call_args[1]["json"]
        expected_messages = [{"role": "user", "content": "Hello, how are you?"}]
        assert json_data["messages"] == expected_messages
    
    @patch('requests.post')
    def test_simple_request_with_messages(self, mock_post, azure_client, mock_azure_response_data):
        """测试简化请求方法使用消息列表"""
        mock_response = Mock()
        mock_response.json.return_value = mock_azure_response_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = azure_client.simple_request(messages, model_name="gpt-4")
        expected_content = mock_azure_response_data['choices'][0]['message']['content']
        assert result == expected_content
        
        # 验证消息直接传递
        call_args = mock_post.call_args
        json_data = call_args[1]["json"]
        assert json_data["messages"] == messages


class TestAzureParameterHandling:
    """测试 Azure 参数处理逻辑"""
    
    def test_none_values_excluded(self, azure_client):
        """测试 None 值被排除"""
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(
            messages,
            temperature=None,
            max_tokens=100,
            top_p=None
        )
        
        assert "temperature" not in data
        assert "top_p" not in data
        assert data["max_tokens"] == 100
    
    def test_config_fallback(self, azure_client):
        """测试配置回退机制"""
        # 设置一些配置值
        azure_client.config.temperature = 0.7
        azure_client.config.custom_param = "config_value"
        
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(messages)
        
        # 应该使用配置中的值
        assert data["temperature"] == 0.7
        assert data["custom_param"] == "config_value"
    
    def test_kwargs_override_config(self, azure_client):
        """测试 kwargs 覆盖配置"""
        # 设置配置值
        azure_client.config.temperature = 0.7
        
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(
            messages,
            temperature=0.2  # 覆盖配置
        )
        
        # 应该使用 kwargs 中的值
        assert data["temperature"] == 0.2
    
    def test_stream_default_false(self, azure_client):
        """测试 stream 参数默认为 False"""
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(messages)
        
        assert data["stream"] is False
    
    def test_unknown_parameters_included(self, azure_client):
        """测试未知参数也会被包含"""
        messages = [{"role": "user", "content": "Hello"}]
        data = azure_client._build_chat_data(
            messages,
            future_param="new_feature",
            another_param={"complex": "value"}
        )
        
        assert data["future_param"] == "new_feature"
        assert data["another_param"] == {"complex": "value"}


class TestAzureURLConstruction:
    """测试 Azure URL 构建逻辑"""
    
    def test_url_with_all_params(self):
        """测试包含所有参数的 URL 构建"""
        config = AzureOpenAIConfig(
            api_base="https://test.openai.azure.com/",  # 测试末尾斜杠处理
            api_version="2024-02-15-preview",
            api_key="test-key"
        )
        url = config.get_request_url()
        expected = "https://test.openai.azure.com?api-version=2024-02-15-preview&ak=test-key"
        assert url == expected
    
    def test_url_minimal_params(self):
        """测试最少参数的 URL 构建"""
        config = AzureOpenAIConfig(api_base="https://test.openai.azure.com")
        url = config.get_request_url()
        expected = "https://test.openai.azure.com"
        assert url == expected
