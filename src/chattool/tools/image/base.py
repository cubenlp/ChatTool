from abc import ABC, abstractmethod
from typing import Optional, Any

class ImageGenerator(ABC):
    """
    Abstract base class for all image generation tools.
    """
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Any:
        """
        Generate an image from the given prompt.
        
        Args:
            prompt (str): The text description for the image.
            **kwargs: Additional parameters specific to the implementation (e.g. style, size).
            
        Returns:
            Any: The result object (e.g. image URL, bytes, or file path).
        """
        pass

    def get_models(self) -> list:
        """
        Get available models for image generation.
        
        Returns:
            list: A list of available model IDs or objects.
        """
        return []
