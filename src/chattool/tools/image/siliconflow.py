
import os
import requests
from typing import Optional, Any
from .base import ImageGenerator
from chattool.config import SiliconFlowConfig

class SiliconFlowImageGenerator(ImageGenerator):
    """
    Wrapper for SiliconFlow Image Generation (OpenAI-compatible).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or SiliconFlowConfig.SILICONFLOW_API_KEY.value
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY not set")
        
        self.api_base = "https://api.siliconflow.cn/v1"

    def generate(self, prompt: str, model: Optional[str] = None, size: str = "1024x1024", **kwargs) -> Any:
        """
        Generate image using SiliconFlow API.
        
        Args:
            prompt (str): Text description.
            model (str): Model name.
            size (str): Image size (e.g., 1024x1024).
            **kwargs: Additional parameters.
            
        Returns:
            list: List of image URLs.
        """
        model = model or SiliconFlowConfig.SILICONFLOW_MODEL_ID.value or "black-forest-labs/FLUX.1-schnell"
        
        url = f"{self.api_base}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Adjust parameters for SiliconFlow
        payload = {
            "model": model,
            "prompt": prompt,
            "image_size": size,
            "batch_size": 1,
            **kwargs
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code != 200:
                raise Exception(f"API Error ({response.status_code}): {response.text}")
                
            data = response.json()
            
            # SiliconFlow format: {'images': [{'url': ...}]}
            if 'images' in data:
                 return [img['url'] for img in data['images']]
            # OpenAI standard format: {'data': [{'url': ...}]}
            elif 'data' in data:
                 return [img['url'] for img in data['data']]
            else:
                raise Exception(f"Unknown response format: {data}")
                
        except Exception as e:
            raise Exception(f"SiliconFlow generation failed: {e}")

    def get_models(self) -> list[dict]:
        """
        Get list of available image models.
        API: https://api.siliconflow.cn/v1/models?type=image
        """
        url = f"{self.api_base}/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        params = {"type": "image"}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code != 200:
                raise Exception(f"API Error ({response.status_code}): {response.text}")
                
            data = response.json()
            if 'data' in data:
                return data['data']
            return []
            
        except Exception as e:
            raise Exception(f"Failed to fetch models: {e}")
