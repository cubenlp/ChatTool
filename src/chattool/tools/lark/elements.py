import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class MessageType:
    """
    Message types supported by Lark/Feishu Open Platform.
    See: https://open.feishu.cn/document/server-docs/im-v1/message-content-description/create_json
    """
    TEXT = "text"          # 文本消息
    POST = "post"          # 富文本消息
    IMAGE = "image"        # 图片消息
    INTERACTIVE = "interactive" # 卡片消息
    SHARE_CHAT = "share_chat"   # 分享群名片
    SHARE_USER = "share_user"   # 分享个人名片
    AUDIO = "audio"        # 语音消息
    MEDIA = "media"        # 视频消息
    FILE = "file"          # 文件消息
    STICKER = "sticker"    # 表情包消息

class BaseMessage(ABC):
    def __init__(self, msg_type: str):
        self.msg_type = msg_type

    @abstractmethod
    def _to_dict(self) -> Dict[str, Any]:
        """Convert message content to dictionary"""
        pass

    def to_json(self) -> str:
        """Convert message content to JSON string for API"""
        return json.dumps(self._to_dict(), ensure_ascii=False)

class TextMessage(BaseMessage):
    def __init__(self, content: str):
        super().__init__(MessageType.TEXT)
        self.content = content

    def _to_dict(self) -> Dict[str, Any]:
        return {"text": self.content}

class ImageMessage(BaseMessage):
    def __init__(self, image_key: str):
        super().__init__(MessageType.IMAGE)
        self.image_key = image_key

    def _to_dict(self) -> Dict[str, Any]:
        return {"image_key": self.image_key}

class PostMessage(BaseMessage):
    def __init__(self, title: str, content: List[List[Dict[str, Any]]]):
        super().__init__(MessageType.POST)
        self.title = title
        self.content = content

    def _to_dict(self) -> Dict[str, Any]:
        return {
            "zh_cn": {
                "title": self.title,
                "content": self.content
            }
        }

class InteractiveMessage(BaseMessage):
    def __init__(self, card: Dict[str, Any]):
        super().__init__(MessageType.INTERACTIVE)
        self.card = card

    def _to_dict(self) -> Dict[str, Any]:
        return self.card

class ShareChatMessage(BaseMessage):
    def __init__(self, chat_id: str):
        super().__init__(MessageType.SHARE_CHAT)
        self.chat_id = chat_id

    def _to_dict(self) -> Dict[str, Any]:
        return {"chat_id": self.chat_id}

class ShareUserMessage(BaseMessage):
    def __init__(self, user_id: str):
        super().__init__(MessageType.SHARE_USER)
        self.user_id = user_id

    def _to_dict(self) -> Dict[str, Any]:
        return {"user_id": self.user_id}

class AudioMessage(BaseMessage):
    def __init__(self, file_key: str):
        super().__init__(MessageType.AUDIO)
        self.file_key = file_key

    def _to_dict(self) -> Dict[str, Any]:
        return {"file_key": self.file_key}

class MediaMessage(BaseMessage):
    def __init__(self, file_key: str, image_key: str):
        super().__init__(MessageType.MEDIA)
        self.file_key = file_key
        self.image_key = image_key

    def _to_dict(self) -> Dict[str, Any]:
        return {"file_key": self.file_key, "image_key": self.image_key}

class FileMessage(BaseMessage):
    def __init__(self, file_key: str):
        super().__init__(MessageType.FILE)
        self.file_key = file_key

    def _to_dict(self) -> Dict[str, Any]:
        return {"file_key": self.file_key}

class StickerMessage(BaseMessage):
    def __init__(self, file_key: str):
        super().__init__(MessageType.STICKER)
        self.file_key = file_key

    def _to_dict(self) -> Dict[str, Any]:
        return {"file_key": self.file_key}