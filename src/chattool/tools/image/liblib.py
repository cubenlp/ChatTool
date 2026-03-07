import os
import time
import uuid
import hmac
import hashlib
import base64
import json
from typing import Optional, Any, List, Dict
from .base import ImageGenerator
from chattool.config import LiblibConfig

class LiblibImageGenerator(ImageGenerator):
    """
    Client for LiblibAI Image Generation API.
    
    Requires `LIBLIB_ACCESS_KEY` and `LIBLIB_SECRET_KEY` environment variables.
    """
    
    BASE_URL = "https://openapi.liblibai.cloud"
    GENERATE_URI = "/api/generate/webui/text2img"
    STATUS_URI = "/api/generate/webui/status"

    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.access_key = access_key or LiblibConfig.LIBLIB_ACCESS_KEY.value
        self.secret_key = secret_key or LiblibConfig.LIBLIB_SECRET_KEY.value
        # Attempt to load default model ID from config if not provided in generate call
        self.default_model_id = LiblibConfig.LIBLIB_MODEL_ID.value 
        if not self.access_key or not self.secret_key:
            raise ValueError("LIBLIB_ACCESS_KEY or LIBLIB_SECRET_KEY not set")

    def _make_sign(self, uri: str, timestamp: str, nonce: str) -> str:
        """
        Generate HMAC-SHA1 signature.
        """
        content = '&'.join((uri, timestamp, nonce))
        digest = hmac.new(self.secret_key.encode('utf-8'), content.encode('utf-8'), hashlib.sha1).digest()
        sign = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('utf-8')
        return sign

    def _request(self, method: str, uri: str, data: Optional[Dict] = None) -> Dict:
        """
        Make a signed request to LiblibAI API.
        """
        import requests
        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4()).replace('-', '')
        sign = self._make_sign(uri, timestamp, nonce)
        
        url = f"{self.BASE_URL}{uri}"
        params = {
            "AccessKey": self.access_key,
            "Signature": sign,
            "Timestamp": timestamp,
            "SignatureNonce": nonce
        }
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, params=params, json=data, headers=headers)
            else:
                response = requests.get(url, params=params, headers=headers)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"LiblibAI API Error: {result.get('msg')} (Code: {result.get('code')})")
                
            return result
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def generate(self, prompt: str, model_id: str = None, **kwargs) -> Any:
        """
        Generate image using LiblibAI.
        
        Args:
            prompt (str): Text description.
            model_id (str): Checkpoint or Model ID in LiblibAI. Required.
            **kwargs: Additional parameters (sampler, steps, cfg_scale, width, height, lora_weights).
            
        Returns:
            str: The image URL.
        """
        # Use provided model_id, or fall back to default from config
        model_id = model_id or self.default_model_id
        
        if not model_id:
             raise ValueError("model_id is required for LiblibImageGenerator. Provide it via argument or set LIBLIB_MODEL_ID env var.")

        # 1. Submit Task
        payload = {
            "templateUuid": kwargs.get("templateUuid", ""),
            "generateParams": {
                "checkPointId": model_id,
                "prompt": prompt,
                "negativePrompt": kwargs.get("negative_prompt", ""),
                "width": kwargs.get("width", 512),
                "height": kwargs.get("height", 512),
                "steps": kwargs.get("steps", 20),
                "sampler": kwargs.get("sampler", 15),
                "cfgScale": kwargs.get("cfg_scale", 7),
                "imgCount": 1,
                "restoreFaces": kwargs.get("restore_faces", 0),
            }
        }
        
        print(f"Submitting task to LiblibAI for model {model_id}...")
        response = self._request("POST", self.GENERATE_URI, payload)
        generate_uuid = response.get("data", {}).get("generateUuid")
        
        if not generate_uuid:
            raise Exception("Failed to get generateUuid from response")
            
        print(f"Task submitted. UUID: {generate_uuid}. Polling for result...")
        
        # 2. Poll for Result
        max_retries = 60
        for _ in range(max_retries):
            status_resp = self._request("POST", self.STATUS_URI, {"generateUuid": generate_uuid})
            data = status_resp.get("data", {})
            status = data.get("generateStatus") # 1: waiting, 2: generating, 3: success, 4: failed (Assumed)
            
            images = data.get("images", [])
            if images:
                return images[0].get("imageUrl")
                
            # Check for failure status if known, or just rely on timeout/images
            if status == 4: 
                 raise Exception(f"Generation failed: {data}")

            time.sleep(2)
            
        raise Exception("Timeout waiting for image generation")

    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get available models for image generation.
        
        Returns:
            list: A list of available model objects.
        """
        # Placeholder list since no public list endpoint is easily available without auth/reverse engineering
        return [
            {"id": "ba34a22f1c044472a42b6051aac2afb3", "name": "Sim Portrait Atmosphere Photo XL-lora"},
            {"id": "liblib-sdxl-model", "name": "Stable Diffusion XL (Liblib)"},
            {"id": "liblib-realistic-vision", "name": "Realistic Vision V6.0"},
        ]
