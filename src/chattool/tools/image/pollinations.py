
import random
from typing import Optional, Any
from urllib.parse import quote
import requests
from .base import ImageGenerator
from chattool.config import PollinationsConfig

class PollinationsImageGenerator(ImageGenerator):
    """
    Wrapper for Pollinations.ai Image Generation.
    
    API: https://gen.pollinations.ai/image/{prompt}
    """

    def __init__(self, model: Optional[str] = None):
        self.model = model or PollinationsConfig.POLLINATIONS_MODEL_ID.value or "flux"
        self.api_key = PollinationsConfig.POLLINATIONS_API_KEY.value
        if not self.api_key:
            raise ValueError("POLLINATIONS_API_KEY not set")
        self.base_url = "https://gen.pollinations.ai/image"

    def generate(self, prompt: str, width: int = 1024, height: int = 1024, seed: Optional[int] = None, **kwargs) -> Any:
        """
        Generate image using Pollinations.ai.
        
        Args:
            prompt (str): Text description.
            width (int): Image width.
            height (int): Image height.
            seed (int, optional): Random seed.
            **kwargs: Additional parameters.
            
        Returns:
            list: List of image URLs (Pollinations returns a direct URL).
        """
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
            
        encoded_prompt = quote(prompt)
        url = f"{self.base_url}/{encoded_prompt}?width={width}&height={height}&model={self.model}&seed={seed}"
        
        return [url]

    def get_models(self) -> list[dict]:
        url = "https://gen.pollinations.ai/image/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch models: {response.status_code} - {response.text}")
        data = response.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return []
