import os
import pytest
import sys
from unittest.mock import MagicMock, patch
from chattool.tools.image import create_generator
from chattool.tools.image.tongyi import TongyiImageGenerator
from chattool.tools.image.huggingface import HuggingFaceImageGenerator
from chattool.tools.image.liblib import LiblibImageGenerator
from chattool.tools.image.bing import BingImageGenerator
from chattool.config import TongyiConfig, HuggingFaceConfig, LiblibConfig, BingConfig

class TestImageGenerators:

    def test_factory_tongyi(self):
        with patch.object(TongyiConfig.DASHSCOPE_API_KEY, 'value', "test_key"):
            gen = create_generator("tongyi")
            assert isinstance(gen, TongyiImageGenerator)
            assert gen.api_key == "test_key"

    def test_factory_huggingface(self):
        with patch.object(HuggingFaceConfig.HUGGINGFACE_HUB_TOKEN, 'value', "test_token"):
            gen = create_generator("huggingface")
            assert isinstance(gen, HuggingFaceImageGenerator)
            assert gen.api_key == "test_token"
    
    def test_factory_liblib(self):
        with patch.object(LiblibConfig.LIBLIB_ACCESS_KEY, 'value', "ak"), \
             patch.object(LiblibConfig.LIBLIB_SECRET_KEY, 'value', "sk"):
            gen = create_generator("liblib")
            assert isinstance(gen, LiblibImageGenerator)
            assert gen.access_key == "ak"
            assert gen.secret_key == "sk"

    def test_factory_bing(self):
        with patch.object(BingConfig.BING_COOKIE_U, 'value', "cookie"):
            gen = create_generator("bing")
            assert isinstance(gen, BingImageGenerator)
            assert gen.cookie_u == "cookie"

    def test_factory_unknown(self):
        with pytest.raises(ValueError):
            create_generator("unknown")

    def test_tongyi_generate(self):
        # We need to mock dashscope import inside the method
        with patch.object(TongyiConfig.DASHSCOPE_API_KEY, 'value', "test_key"):
            # Mock dashscope module
            mock_dashscope = MagicMock()
            mock_dashscope.ImageSynthesis.Models.wanx_v1 = "wanx-v1"
            
            # Mock response
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.output.results = [{"url": "http://example.com/image.png"}]
            mock_dashscope.ImageSynthesis.call.return_value = mock_resp
            
            # Patch sys.modules to return our mock when dashscope is imported
            with patch.dict(sys.modules, {'dashscope': mock_dashscope}):
                gen = TongyiImageGenerator()
                result = gen.generate("test prompt")
                
                assert result == [{"url": "http://example.com/image.png"}]
                mock_dashscope.ImageSynthesis.call.assert_called_once()

    @patch("chattool.tools.image.huggingface.requests.post")
    def test_huggingface_generate(self, mock_post):
        with patch.object(HuggingFaceConfig.HUGGINGFACE_HUB_TOKEN, 'value', "test_token"):
            gen = HuggingFaceImageGenerator()
            
            # Mock success response
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"fake_image_bytes"
            mock_post.return_value = mock_resp
            
            result = gen.generate("test prompt")
            assert result == b"fake_image_bytes"
            mock_post.assert_called_once()
