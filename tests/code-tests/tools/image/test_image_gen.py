import os
import pytest
import sys
from unittest.mock import MagicMock, patch
from chattool.tools.image import create_generator
from chattool.tools.image.tongyi import TongyiImageGenerator
from chattool.tools.image.huggingface import HuggingFaceImageGenerator
from chattool.tools.image.liblib import LiblibImageGenerator
from chattool.config import TongyiConfig, HuggingFaceConfig, LiblibConfig

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

    def test_liblib_generate_flow(self):
        with patch.object(LiblibConfig.LIBLIB_ACCESS_KEY, 'value', "ak"), \
             patch.object(LiblibConfig.LIBLIB_SECRET_KEY, 'value', "sk"):
            gen = LiblibImageGenerator()
            
            # Mock requests
            with patch("requests.post") as mock_post:
                # 1. Submit task response
                mock_submit_resp = MagicMock()
                mock_submit_resp.status_code = 200
                mock_submit_resp.json.return_value = {
                    "code": 0,
                    "data": {"generateUuid": "uuid-123"}
                }
                
                # 2. Poll status response (waiting)
                mock_status_waiting = MagicMock()
                mock_status_waiting.status_code = 200
                mock_status_waiting.json.return_value = {
                    "code": 0,
                    "data": {"generateStatus": 1, "images": []}
                }
                
                # 3. Poll status response (success)
                mock_status_success = MagicMock()
                mock_status_success.status_code = 200
                mock_status_success.json.return_value = {
                    "code": 0,
                    "data": {
                        "generateStatus": 3,
                        "images": [{"imageUrl": "http://example.com/liblib.png"}]
                    }
                }
                
                # Sequence of side effects
                mock_post.side_effect = [
                    mock_submit_resp,
                    mock_status_waiting,
                    mock_status_success
                ]
                
                # We need to mock time.sleep to avoid waiting
                with patch("time.sleep"):
                    result = gen.generate("prompt", model_id="model-123")
                    
                assert result == "http://example.com/liblib.png"
                assert mock_post.call_count == 3

    def test_liblib_generate_with_default_model_id(self):
         with patch.object(LiblibConfig.LIBLIB_ACCESS_KEY, 'value', "ak"), \
             patch.object(LiblibConfig.LIBLIB_SECRET_KEY, 'value', "sk"), \
             patch.object(LiblibConfig.LIBLIB_MODEL_ID, 'value', "default-model-id"):
            
            gen = LiblibImageGenerator()
            
            # Mock requests
            with patch("requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                
                # Mock _request to avoid complex side effects
                with patch.object(gen, '_request') as mock_request:
                     # Mock _request to return success immediately on status poll
                     mock_request.side_effect = [
                         {"data": {"generateUuid": "uuid"}}, # submit
                         {"data": {"generateStatus": 3, "images": [{"imageUrl": "url"}]}} # status
                     ]

                     with patch("time.sleep"):
                         gen.generate("prompt") # No model_id provided
                     
                     # Check if submit called with default model id
                     args, _ = mock_request.call_args_list[0]
                     # args[2] is payload (since _request(method, uri, data))
                     payload = args[2]
                     assert payload["generateParams"]["checkPointId"] == "default-model-id"

    def test_liblib_get_models(self):
        with patch.object(LiblibConfig.LIBLIB_ACCESS_KEY, 'value', "ak"), \
             patch.object(LiblibConfig.LIBLIB_SECRET_KEY, 'value', "sk"):
            gen = LiblibImageGenerator()
            models = gen.get_models()
            assert isinstance(models, list)
            assert len(models) > 0
            assert "id" in models[0]
