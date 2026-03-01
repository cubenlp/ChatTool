import os
import requests
from typing import Optional, Any
from .base import ImageGenerator

class HuggingFaceImageGenerator(ImageGenerator):
    """
    Client for Hugging Face Inference API (Text-to-Image).
    
    Requires `HUGGINGFACE_HUB_TOKEN` environment variable for authenticated requests.
    """
    
    DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell"
    API_URL_TEMPLATE = "https://api-inference.huggingface.co/models/{model_id}"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUGGINGFACE_HUB_TOKEN")
        if not self.api_key:
            raise ValueError("HUGGINGFACE_HUB_TOKEN environment variable not set or api_key not provided")

    def generate(self, prompt: str, model_id: str = DEFAULT_MODEL, **kwargs) -> Any:
        """
        Generate image using Hugging Face Inference API.
        
        Args:
            prompt (str): Text description.
            model_id (str): Hugging Face model ID (e.g., "black-forest-labs/FLUX.1-schnell").
            **kwargs: Additional parameters for the model (e.g., negative_prompt, guidance_scale, width, height).
            
        Returns:
            bytes: The generated image bytes.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": prompt, "parameters": kwargs}
        
        url = self.API_URL_TEMPLATE.format(model_id=model_id)
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Failed to generate image: {response.status_code} - {response.text}")
