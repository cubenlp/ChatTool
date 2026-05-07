"""AzureConfig env schema."""

from .base import BaseEnvConfig, EnvField


class AzureConfig(BaseEnvConfig):
    _title = "Azure OpenAI Configuration"
    _aliases = ["azure", "az"]
    _storage_dir = "Azure"

    AZURE_OPENAI_API_KEY = EnvField("AZURE_OPENAI_API_KEY", desc="Azure OpenAI API Key", is_sensitive=True)
    AZURE_OPENAI_ENDPOINT = EnvField("AZURE_OPENAI_ENDPOINT", desc="Azure OpenAI Endpoint")
    AZURE_OPENAI_API_VERSION = EnvField("AZURE_OPENAI_API_VERSION", desc="Azure OpenAI API Version")
    AZURE_OPENAI_API_MODEL = EnvField("AZURE_OPENAI_API_MODEL", desc="Azure OpenAI Deployment Name (Model)")

    @classmethod
    def test(cls):
        print(f"Testing {cls._title}...")
        try:
            from chattool.llm.chattype import AzureChat
            chat = AzureChat(messages=[{"role": "user", "content": "hi"}])
            resp = chat.get_response(max_tokens=5)
            print(f"✅ Success! Response: {resp.content}")
        except Exception as e:
            print(f"❌ Failed: {e}")


__all__ = ["AzureConfig"]
