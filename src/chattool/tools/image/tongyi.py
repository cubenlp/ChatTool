import os
import requests
from typing import Optional, Any
from .base import ImageGenerator

class TongyiImageGenerator(ImageGenerator):
    """
    Client for Tongyi Wanxiang (Alibaba Cloud DashScope) Image Generation API.
    
    Requires `DASHSCOPE_API_KEY` environment variable.
    """
    
    API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable not set or api_key not provided")

    def generate(self, prompt: str, style: str = "<auto>", size: str = "1024*1024", n: int = 1) -> Any:
        """
        Generate image using Tongyi Wanxiang.
        
        Args:
            prompt (str): Text description.
            style (str): Style preset (e.g. "<auto>", "<3d cartoon>", "<anime>", "<oil painting>", "<watercolor>", "<sketch>").
            size (str): Image size (e.g. "1024*1024", "1280*720").
            n (int): Number of images to generate (default 1).
            
        Returns:
            dict: The JSON response from DashScope API containing image URLs.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"  # Enable async task submission if needed, but for simple generation we might use sync endpoint if available. Actually Tongyi usually uses task submission for image generation.
        }
        
        # Note: Tongyi Wanxiang usually requires task submission -> polling.
        # This is a simplified example assuming a direct generation endpoint or task submission.
        # For production, use the official SDK: `dashscope.ImageSynthesis.call(...)`
        
        # If dashscope SDK is available, prefer using it.
        try:
            import dashscope
            dashscope.api_key = self.api_key
            rsp = dashscope.ImageSynthesis.call(
                model=dashscope.ImageSynthesis.Models.wanx_v1,
                prompt=prompt,
                style=style,
                size=size,
                n=n
            )
            if rsp.status_code == 200:
                return rsp.output.results # List of dicts with 'url'
            else:
                raise Exception(f"Failed to generate image: {rsp.code} - {rsp.message}")
        except ImportError:
            # Fallback to HTTP request (Task submission flow omitted for brevity, recommending SDK)
            raise ImportError("Please install 'dashscope' package to use TongyiImageGenerator: pip install dashscope")

