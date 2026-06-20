from .base import ImageGenerator
from .tongyi import TongyiImageGenerator
from .huggingface import HuggingFaceImageGenerator
from .liblib import LiblibImageGenerator
from .pollinations import PollinationsImageGenerator
from .siliconflow import SiliconFlowImageGenerator
from .codex import CodexImageGenerator

__all__ = [
    "ImageGenerator",
    "TongyiImageGenerator",
    "HuggingFaceImageGenerator",
    "LiblibImageGenerator",
    "PollinationsImageGenerator",
    "SiliconFlowImageGenerator",
    "CodexImageGenerator",
]

def create_generator(provider: str, **kwargs) -> ImageGenerator:
    """
    Factory function to create an image generator instance.
    
    Args:
        provider (str): 'tongyi', 'huggingface', 'liblib', 'pollinations',
            'siliconflow', 'codex', or 'openai-codex'
        **kwargs: Additional config (api_key, etc.)
        
    Returns:
        ImageGenerator: The initialized generator.
    """
    if provider == "tongyi":
        return TongyiImageGenerator(**kwargs)
    elif provider == "huggingface":
        return HuggingFaceImageGenerator(**kwargs)
    elif provider == "liblib":
        return LiblibImageGenerator(**kwargs)
    elif provider == "pollinations":
        return PollinationsImageGenerator(**kwargs)
    elif provider == "siliconflow":
        return SiliconFlowImageGenerator(**kwargs)
    elif provider in {"codex", "openai-codex"}:
        return CodexImageGenerator(**kwargs)

    else:
        raise ValueError(f"Unknown provider: {provider}")
