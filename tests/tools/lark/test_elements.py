import pytest
import json
from chattool.tools.lark.elements import (
    MessageType, BaseMessage, TextMessage, ImageMessage, PostMessage,
    InteractiveMessage, ShareChatMessage, ShareUserMessage,
    AudioMessage, MediaMessage, FileMessage, StickerMessage
)

@pytest.mark.lark
class TestLarkElements:
    def test_text_message(self):
        msg = TextMessage("Hello World")
        assert msg.msg_type == MessageType.TEXT
        assert msg.content == "Hello World"
        assert json.loads(msg.to_json()) == {"text": "Hello World"}

    def test_image_message(self):
        msg = ImageMessage("img_123")
        assert msg.msg_type == MessageType.IMAGE
        assert msg.image_key == "img_123"
        assert json.loads(msg.to_json()) == {"image_key": "img_123"}

    def test_post_message(self):
        content = [[{"tag": "text", "text": "hello"}]]
        msg = PostMessage("Title", content)
        assert msg.msg_type == MessageType.POST
        assert msg.title == "Title"
        assert msg.content == content
        expected = {
            "zh_cn": {
                "title": "Title",
                "content": content
            }
        }
        assert json.loads(msg.to_json()) == expected

    def test_interactive_message(self):
        card = {"elements": []}
        msg = InteractiveMessage(card)
        assert msg.msg_type == MessageType.INTERACTIVE
        assert msg.card == card
        assert json.loads(msg.to_json()) == card

    def test_share_chat_message(self):
        msg = ShareChatMessage("chat_123")
        assert msg.msg_type == MessageType.SHARE_CHAT
        assert msg.chat_id == "chat_123"
        assert json.loads(msg.to_json()) == {"chat_id": "chat_123"}

    def test_share_user_message(self):
        msg = ShareUserMessage("user_123")
        assert msg.msg_type == MessageType.SHARE_USER
        assert msg.user_id == "user_123"
        assert json.loads(msg.to_json()) == {"user_id": "user_123"}

    def test_audio_message(self):
        msg = AudioMessage("file_123")
        assert msg.msg_type == MessageType.AUDIO
        assert msg.file_key == "file_123"
        assert json.loads(msg.to_json()) == {"file_key": "file_123"}

    def test_media_message(self):
        msg = MediaMessage("file_123", "img_123")
        assert msg.msg_type == MessageType.MEDIA
        assert msg.file_key == "file_123"
        assert msg.image_key == "img_123"
        assert json.loads(msg.to_json()) == {"file_key": "file_123", "image_key": "img_123"}

    def test_file_message(self):
        msg = FileMessage("file_123")
        assert msg.msg_type == MessageType.FILE
        assert msg.file_key == "file_123"
        assert json.loads(msg.to_json()) == {"file_key": "file_123"}

    def test_sticker_message(self):
        msg = StickerMessage("file_123")
        assert msg.msg_type == MessageType.STICKER
        assert msg.file_key == "file_123"
        assert json.loads(msg.to_json()) == {"file_key": "file_123"}
