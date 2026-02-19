import json
import logging
import httpx
import os
from typing import List, Dict, Optional, Any, Union
from chattool.config import ZulipConfig

class ZulipClient:
    """
    Zulip Client implementation referenced from the official python-zulip-api SDK.
    Uses httpx for HTTP requests and mimics the SDK's parameter serialization logic.
    """

    def __init__(self):
        # Load configuration using the project's standard config system
        self.site = ZulipConfig.ZULIP_SITE.value
        self.email = ZulipConfig.ZULIP_BOT_EMAIL.value
        self.api_key = ZulipConfig.ZULIP_BOT_API_KEY.value

        if not all([self.site, self.email, self.api_key]):
            raise ValueError(
                "Missing Zulip credentials. Please ensure ZULIP_SITE, ZULIP_BOT_EMAIL, "
                "and ZULIP_BOT_API_KEY are set in your environment or .env file."
            )

        # Normalize URL
        self.base_url = self.site.rstrip("/") + "/api/v1"
        self.auth = (self.email, self.api_key)
        
        # Initialize HTTP client
        self.client = httpx.Client(auth=self.auth, timeout=30.0)
        self.logger = logging.getLogger("ZulipClient")

    def _prepare_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare parameters for the API request.
        Mimics the official SDK's `do_api_query` logic:
        - String values are kept as-is.
        - Non-string values (lists, dicts, bools, ints) are JSON-encoded.
        """
        prepared = {}
        for key, value in params.items():
            if value is None:
                continue
            
            if isinstance(value, str):
                prepared[key] = value
            else:
                prepared[key] = json.dumps(value)
        return prepared

    def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None, files: Dict = None) -> Dict[str, Any]:
        """
        Internal request helper.
        """
        url = f"{self.base_url}{endpoint}"
        
        # Prepare data/params
        # For GET, we use 'params', for POST/PATCH etc we use 'data' (form-encoded)
        kwargs = {}
        if params:
            prepared_params = self._prepare_params(params)
            if method.upper() == "GET":
                kwargs["params"] = prepared_params
            else:
                kwargs["data"] = prepared_params

        if files:
            kwargs["files"] = files

        try:
            response = self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
            raise Exception(f"Zulip API Error ({e.response.status_code}): {e.response.text}") from e
        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise

    def send_message(self, type: str, to: Union[str, List[int], List[str]], content: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a stream or private message.
        
        Args:
            type: "stream" or "private"
            to: Stream name (str) for streams; List of user IDs or emails for private.
            content: The message content.
            topic: The topic name (required for stream messages).
        """
        data = {
            "type": type,
            "to": to,
            "content": content
        }
        if topic:
            data["topic"] = topic

        return self._request("POST", "/messages", params=data)

    def get_messages(self, 
                     anchor: Union[int, str] = "newest", 
                     num_before: int = 20, 
                     num_after: int = 0, 
                     narrow: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve messages from a stream or conversation.
        """
        params = {
            "anchor": anchor,
            "num_before": num_before,
            "num_after": num_after,
            "apply_markdown": False
        }
        if narrow:
            params["narrow"] = narrow

        result = self._request("GET", "/messages", params=params)
        return result.get("messages", [])

    def list_streams(self, include_public: bool = True) -> List[Dict[str, Any]]:
        """
        List all streams.
        """
        params = {"include_public": include_public}
        result = self._request("GET", "/streams", params=params)
        return result.get("streams", [])

    def react_to_message(self, message_id: int, emoji_name: str, reaction_type: str = "unicode") -> Dict[str, Any]:
        """
        Add a reaction to a message.
        """
        data = {
            "emoji_name": emoji_name,
            "reaction_type": reaction_type
        }
        return self._request("POST", f"/messages/{message_id}/reactions", params=data)

    def get_profile(self) -> Dict[str, Any]:
        """
        Get current user profile.
        """
        return self._request("GET", "/users/me")

    def upload_file(self, file_path: str) -> str:
        """
        Upload a file to Zulip. Returns the URI.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            # httpx handles file uploads; we don't need _prepare_params for the file itself
            # but we pass it as 'files' argument
            files = {"file": f}
            # Note: The SDK endpoint is /user_uploads
            url = f"{self.base_url}/user_uploads"
            response = self.client.post(url, files=files)
            response.raise_for_status()
            return response.json().get("uri")
