import json
import lark_oapi
from lark_oapi.api.im.v1 import (
    CreateMessageRequest, CreateMessageRequestBody,
    GetChatRequest, GetChatMembersRequest
)
from chattool.config.main import FeishuConfig
from chattool.tools.lark.elements import BaseMessage

class LarkBot:
    """Lark Bot class for interacting with Feishu/Lark Open Platform."""

    def __init__(self, config: FeishuConfig = None):
        """Initialize the LarkBot with FeishuConfig.

        Args:
            config (FeishuConfig, optional): The configuration object. Defaults to None.
        """
        if config is None:
            self.config = FeishuConfig()
        else:
            self.config = config

        # Initialize the Lark client
        # Note: lark-oapi uses a builder pattern for client initialization
        builder = lark_oapi.Client.builder() \
            .app_id(self.config.FEISHU_APP_ID.value) \
            .app_secret(self.config.FEISHU_APP_SECRET.value) \
            .log_level(lark_oapi.LogLevel.INFO)
            
        if self.config.FEISHU_API_BASE.value:
            builder.domain(self.config.FEISHU_API_BASE.value)
            
        self.client = builder.build()

    def _send_message(self, receive_id: str, receive_id_type: str, msg_type: str, content: str):
        """Internal method to send message.

        Args:
            receive_id (str): The receive ID.
            receive_id_type (str): The receive ID type (open_id, user_id, union_id, email, chat_id).
            msg_type (str): The message type (text, post, image, interactive, etc.).
            content (str): The JSON string content.
        
        Returns:
            response: The response from Lark API.
        """
        # Construct request body
        request_body = CreateMessageRequestBody.builder() \
            .receive_id(receive_id) \
            .msg_type(msg_type) \
            .content(content) \
            .build()

        # Construct request
        request = CreateMessageRequest.builder() \
            .receive_id_type(receive_id_type) \
            .request_body(request_body) \
            .build()

        # Send request
        response = self.client.im.v1.message.create(request)

        # Log result
        if not response.success():
            lark_oapi.logger.error(
                f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
            )
        else:
            # Check if response.data is None
            msg_id = response.data.message_id if response.data else "unknown"
            lark_oapi.logger.info(
                f"Message sent successfully, msg_id: {msg_id}"
            )
        
        return response

    def send_message(self, receive_id: str, receive_id_type: str, message: BaseMessage):
        """Send a message object.

        Args:
            receive_id (str): The receive ID.
            receive_id_type (str): The receive ID type (open_id, user_id, union_id, email, chat_id).
            message (BaseMessage): The message object to send.

        Returns:
            response: The response from Lark API.
        """
        return self._send_message(receive_id, receive_id_type, message.msg_type, message.to_json())

    def send_text(self, receive_id: str, receive_id_type: str, text: str):
        """Send a text message.

        Args:
            receive_id (str): The receive ID.
            receive_id_type (str): The receive ID type.
            text (str): The text content.
        """
        content = json.dumps({"text": text})
        return self._send_message(receive_id, receive_id_type, "text", content)

    def send_post(self, receive_id: str, receive_id_type: str, content: dict):
        """Send a post (rich text) message.

        Args:
            receive_id (str): The receive ID.
            receive_id_type (str): The receive ID type.
            content (dict): The post content structure.
        """
        msg_content = json.dumps(content)
        return self._send_message(receive_id, receive_id_type, "post", msg_content)

    def send_image(self, receive_id: str, receive_id_type: str, image_key: str):
        """Send an image message.

        Args:
            receive_id (str): The receive ID.
            receive_id_type (str): The receive ID type.
            image_key (str): The image key.
        """
        content = json.dumps({"image_key": image_key})
        return self._send_message(receive_id, receive_id_type, "image", content)

    def send_card(self, receive_id: str, receive_id_type: str, card_content: dict):
        """Send an interactive card message.

        Args:
            receive_id (str): The receive ID.
            receive_id_type (str): The receive ID type (open_id, user_id, email, etc.).
            card_content (dict): The card content structure (the JSON object for the card).
        """
        # Note: For interactive messages, the content is just the card JSON string.
        # But if the user passes the card structure, we serialize it.
        content = json.dumps(card_content)
        return self._send_message(receive_id, receive_id_type, "interactive", content)

    def get_chat_info(self, chat_id: str, user_id_type: str = "open_id"):
        """Get chat information.

        Args:
            chat_id (str): The chat ID.
            user_id_type (str, optional): The user ID type. Defaults to "open_id".
        
        Returns:
            response: The response from Lark API.
        """
        # Construct request
        request = GetChatRequest.builder() \
            .chat_id(chat_id) \
            .user_id_type(user_id_type) \
            .build()

        # Send request
        response = self.client.im.v1.chat.get(request)

        # Log result
        if not response.success():
            lark_oapi.logger.error(
                f"client.im.v1.chat.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
            )
        
        return response

    def get_chat_members(self, chat_id: str, member_id_type: str = "open_id", page_size: int = 20, page_token: str = None):
        """Get chat members.

        Args:
            chat_id (str): The chat ID.
            member_id_type (str, optional): The member ID type. Defaults to "open_id".
            page_size (int, optional): The page size. Defaults to 20.
            page_token (str, optional): The page token. Defaults to None.
        
        Returns:
            response: The response from Lark API.
        """
        # Construct request
        builder = GetChatMembersRequest.builder() \
            .chat_id(chat_id) \
            .member_id_type(member_id_type) \
            .page_size(page_size)
            
        if page_token:
            builder.page_token(page_token)
            
        request = builder.build()

        # Send request
        response = self.client.im.v1.chat_members.get(request)

        # Log result
        if not response.success():
            lark_oapi.logger.error(
                f"client.im.v1.chat_members.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
            )
        
        return response

    def get_event_dispatcher(self, encrypt_key: str = None, verification_token: str = None):
        """Get an event dispatcher builder.
        
        Args:
            encrypt_key (str, optional): The encrypt key. Defaults to None.
            verification_token (str, optional): The verification token. Defaults to None.
            
        Returns:
            lark_oapi.EventDispatcherHandler.Builder: The event dispatcher builder.
        """
        return lark_oapi.EventDispatcherHandler.builder(
            encrypt_key or "", 
            verification_token or ""
        )

    def get_bot_info(self):
        """Get bot information.
        
        This method uses the Get Bot Info API (v3) to retrieve bot details.
        https://open.feishu.cn/document/client-docs/bot-v3/bot-overview
        
        Returns:
            response: The response from Lark API.
        """
        # Construct request manually as bot.v3 might not be available in SDK
        request = lark_oapi.BaseRequest.builder() \
            .http_method(lark_oapi.HttpMethod.GET) \
            .uri("/open-apis/bot/v3/info") \
            .token_types({lark_oapi.AccessTokenType.TENANT}) \
            .build()
            
        # Use the client's internal request method
        # Note: client.request is available on the client instance
        return self.client.request(request)

