import os
from typing import Optional, Any
from .base import ImageGenerator

class BingImageGenerator(ImageGenerator):
    """
    Wrapper for Bing Image Creator (DALL-E 3).
    
    This uses the unofficial 'BingImageCreator' package.
    Requires `BING_COOKIE_U` environment variable (The '_U' cookie from bing.com).
    """

    def __init__(self, cookie_u: Optional[str] = None):
        self.cookie_u = cookie_u or os.getenv("BING_COOKIE_U")
        if not self.cookie_u:
            raise ValueError("BING_COOKIE_U environment variable not set or cookie not provided")

    def generate(self, prompt: str, **kwargs) -> Any:
        """
        Generate image using Bing Image Creator.
        
        Args:
            prompt (str): Text description.
            **kwargs: Additional parameters (unused by BingImageCreator currently).
            
        Returns:
            list: List of image URLs.
        """
        try:
            from BingImageCreator import ImageGen
            i = ImageGen(self.cookie_u)
            images = i.get_images(prompt)
            return images
        except ImportError:
            raise ImportError("Please install 'BingImageCreator' package: pip install BingImageCreator")
        except Exception as e:
            raise Exception(f"Bing Image Creator error: {e}")
