import base64
import json
import pytest
import sys
import time
from unittest.mock import MagicMock, patch
from chattool.tools.image import create_generator
from chattool.tools.image.tongyi import TongyiImageGenerator
from chattool.tools.image.huggingface import HuggingFaceImageGenerator
from chattool.tools.image.liblib import LiblibImageGenerator
from chattool.tools.image.codex import CodexImageGenerator
from chattool.config import (
    TongyiConfig,
    HuggingFaceConfig,
    LiblibConfig,
    OpenAIConfig,
)


def _make_fake_jwt(exp: int) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(
        json.dumps({"exp": exp}).encode("utf-8")
    ).decode().rstrip("=")
    return f"{header}.{payload}.signature"

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

    def test_factory_codex(self):
        gen = create_generator("codex")
        alias = create_generator("openai-codex")
        assert isinstance(gen, CodexImageGenerator)
        assert isinstance(alias, CodexImageGenerator)

    def test_factory_unknown(self):
        with pytest.raises(ValueError):
            create_generator("unknown")

    def test_openai_config_contains_oauth_and_image_fields(self):
        assert hasattr(OpenAIConfig, "OPENAI_ACCESS_TOKEN")
        assert hasattr(OpenAIConfig, "OPENAI_REFRESH_TOKEN")
        assert hasattr(OpenAIConfig, "OPENAI_OAUTH_BASE_URL")
        assert hasattr(OpenAIConfig, "OPENAI_ACCESS_TOKEN_EXPIRES_AT")
        assert hasattr(OpenAIConfig, "OPENAI_IMAGE_MODEL")

    def test_openai_codex_config_is_not_exported_as_separate_env_type(self):
        import chattool.config as config

        assert not hasattr(config, "OpenAICodexConfig")

    def test_codex_resolve_access_token_from_openai_config(self):
        token = _make_fake_jwt(int(time.time()) + 3600)
        with patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN, "value", token):
            gen = CodexImageGenerator()
            assert gen.resolve_access_token() == token

    def test_codex_rejects_configured_access_token_when_expires_at_is_past(self):
        token = _make_fake_jwt(int(time.time()) + 3600)
        with patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN, "value", token), \
             patch.object(OpenAIConfig.OPENAI_REFRESH_TOKEN, "value", ""), \
             patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT, "value", "2000-01-01T00:00:00Z"):
            gen = CodexImageGenerator()
            with pytest.raises(ValueError, match="OPENAI_ACCESS_TOKEN_EXPIRES_AT is expired"):
                gen.resolve_access_token()

    def test_codex_accepts_configured_access_token_when_expires_at_is_future(self):
        token = _make_fake_jwt(int(time.time()) + 3600)
        with patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN, "value", token), \
             patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT, "value", "2999-01-01T00:00:00Z"):
            gen = CodexImageGenerator()
            assert gen.resolve_access_token() == token

    def test_codex_refreshes_configured_access_token_when_expires_at_is_past(self, monkeypatch):
        old_token = _make_fake_jwt(int(time.time()) + 3600)
        captured = {}

        def fake_refresh(refresh_token, **kwargs):
            captured["refresh_token"] = refresh_token
            return {
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "access_token_expires_at": "2026-06-29T02:53:17Z",
            }

        monkeypatch.setattr("chattool.tools.image.codex.refresh_openai_oauth_token", fake_refresh)
        with patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN, "value", old_token), \
             patch.object(OpenAIConfig.OPENAI_REFRESH_TOKEN, "value", "old-refresh-token"), \
             patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT, "value", "2000-01-01T00:00:00Z"):
            gen = CodexImageGenerator()
            assert gen.resolve_access_token() == "new-access-token"
            assert OpenAIConfig.OPENAI_ACCESS_TOKEN.value == "new-access-token"
            assert OpenAIConfig.OPENAI_REFRESH_TOKEN.value == "new-refresh-token"
            assert OpenAIConfig.OPENAI_ACCESS_TOKEN_EXPIRES_AT.value == "2026-06-29T02:53:17Z"

        assert captured["refresh_token"] == "old-refresh-token"

    def test_codex_uses_openai_config_for_oauth_base_and_host_model(self):
        token = _make_fake_jwt(int(time.time()) + 3600)
        with patch.object(OpenAIConfig.OPENAI_ACCESS_TOKEN, "value", token), \
             patch.object(OpenAIConfig.OPENAI_API_BASE, "value", "https://example.test/codex"), \
             patch.object(OpenAIConfig.OPENAI_API_MODEL, "value", "gpt-5.5"), \
             patch.object(OpenAIConfig.OPENAI_IMAGE_MODEL, "value", "gpt-image-2-high"):
            gen = CodexImageGenerator()
            assert gen.resolve_access_token() == token
            assert gen.base_url == "https://example.test/codex"
            assert gen.host_model == "gpt-5.5"
            assert gen.image_model == "gpt-image-2-high"

    def test_codex_generate(self, monkeypatch):
        token = _make_fake_jwt(int(time.time()) + 3600)
        image_bytes = b"fake-png"
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        captured = {}

        class FakeResponse:
            status_code = 200
            text = ""

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                return None

            def iter_lines(self):
                payload = json.dumps(
                    {"item": {"type": "image_generation_call", "result": image_b64}}
                )
                return iter(
                    [
                        "event: response.output_item.done",
                        f"data: {payload}",
                        "",
                        "data: [DONE]",
                        "",
                    ]
                )

        class FakeClient:
            def __init__(self, *args, **kwargs):
                captured["client_kwargs"] = kwargs

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def stream(self, method, url, json):
                captured["method"] = method
                captured["url"] = url
                captured["payload"] = json
                return FakeResponse()

        monkeypatch.setattr("chattool.tools.image.codex.httpx.Client", FakeClient)

        gen = CodexImageGenerator(
            access_token=token,
            image_model="gpt-image-2-high",
            aspect_ratio="landscape",
        )
        result = gen.generate("test prompt")

        assert result == image_bytes
        assert captured["method"] == "POST"
        assert captured["url"].endswith("/responses")
        assert captured["payload"]["tools"][0]["size"] == "1536x1024"
        assert captured["payload"]["tools"][0]["quality"] == "high"

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
