from .base import ImageGenerator
from .tongyi import TongyiImageGenerator
from .huggingface import HuggingFaceImageGenerator
from .liblib import LiblibImageGenerator
from .bing import BingImageGenerator

__all__ = [
    "ImageGenerator",
    "TongyiImageGenerator",
    "HuggingFaceImageGenerator",
    "LiblibImageGenerator",
    "BingImageGenerator",
]

def create_generator(provider: str, **kwargs) -> ImageGenerator:
    """
    Factory function to create an image generator instance.
    
    Args:
        provider (str): 'tongyi', 'huggingface', 'liblib', 'bing'
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
    elif provider == "bing":
        return BingImageGenerator(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
