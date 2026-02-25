import unittest
import json
import pytest
from unittest.mock import MagicMock, patch

from chattool.tools.lark.bot import LarkBot
from chattool.tools.lark.elements import TextMessage, PostMessage
from chattool.config.main import FeishuConfig

@pytest.mark.lark
class TestLarkBot(unittest.TestCase):
    def setUp(self):
        # Start patches
        self.patcher_lark_oapi = patch('chattool.tools.lark.bot.lark_oapi')
        self.patcher_create_msg_req = patch('chattool.tools.lark.bot.CreateMessageRequest')
        self.patcher_create_msg_body = patch('chattool.tools.lark.bot.CreateMessageRequestBody')
        self.patcher_get_chat_req = patch('chattool.tools.lark.bot.GetChatRequest')
        self.patcher_get_members_req = patch('chattool.tools.lark.bot.GetChatMembersRequest')

        self.mock_lark_oapi = self.patcher_lark_oapi.start()
        self.mock_create_msg_req = self.patcher_create_msg_req.start()
        self.mock_create_msg_body = self.patcher_create_msg_body.start()
        self.mock_get_chat_req = self.patcher_get_chat_req.start()
        self.mock_get_members_req = self.patcher_get_members_req.start()

        # Mock Config
        self.mock_config = MagicMock(spec=FeishuConfig)
        self.mock_config.FEISHU_APP_ID.value = "fake_app_id"
        self.mock_config.FEISHU_APP_SECRET.value = "fake_app_secret"
        
        # Setup the builder chain mock for Client
        self.mock_builder = MagicMock()
        self.mock_client_instance = MagicMock()
        
        self.mock_lark_oapi.Client.builder.return_value = self.mock_builder
        self.mock_builder.app_id.return_value = self.mock_builder
        self.mock_builder.app_secret.return_value = self.mock_builder
        self.mock_builder.log_level.return_value = self.mock_builder
        self.mock_builder.build.return_value = self.mock_client_instance
        
        # Setup mocks for Request Builders
        self.setup_request_mocks()

        self.bot = LarkBot(config=self.mock_config)

    def tearDown(self):
        patch.stopall()

    def setup_request_mocks(self):
        # CreateMessageRequestBody
        self.mock_msg_body_builder = MagicMock()
        self.mock_msg_body = MagicMock()
        self.mock_create_msg_body.builder.return_value = self.mock_msg_body_builder
        self.mock_msg_body_builder.receive_id.return_value = self.mock_msg_body_builder
        self.mock_msg_body_builder.msg_type.return_value = self.mock_msg_body_builder
        self.mock_msg_body_builder.content.return_value = self.mock_msg_body_builder
        self.mock_msg_body_builder.build.return_value = self.mock_msg_body

        # CreateMessageRequest
        self.mock_msg_req_builder = MagicMock()
        self.mock_msg_req = MagicMock()
        self.mock_create_msg_req.builder.return_value = self.mock_msg_req_builder
        self.mock_msg_req_builder.receive_id_type.return_value = self.mock_msg_req_builder
        self.mock_msg_req_builder.request_body.return_value = self.mock_msg_req_builder
        self.mock_msg_req_builder.build.return_value = self.mock_msg_req

        # GetChatRequest
        self.mock_chat_req_builder = MagicMock()
        self.mock_chat_req = MagicMock()
        self.mock_get_chat_req.builder.return_value = self.mock_chat_req_builder
        self.mock_chat_req_builder.chat_id.return_value = self.mock_chat_req_builder
        self.mock_chat_req_builder.user_id_type.return_value = self.mock_chat_req_builder
        self.mock_chat_req_builder.build.return_value = self.mock_chat_req

        # GetChatMembersRequest
        self.mock_members_req_builder = MagicMock()
        self.mock_members_req = MagicMock()
        self.mock_get_members_req.builder.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.chat_id.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.member_id_type.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.page_size.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.page_token.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.build.return_value = self.mock_members_req

    def test_init(self):
        """Test initialization of LarkBot."""
        self.mock_lark_oapi.Client.builder.assert_called_once()
        self.mock_builder.app_id.assert_called_with("fake_app_id")
        self.mock_builder.app_secret.assert_called_with("fake_app_secret")
        self.mock_builder.log_level.assert_called_with(self.mock_lark_oapi.LogLevel.INFO)
        # Verify domain is called because mock config returns a truthy mock for FEISHU_API_BASE
        self.mock_builder.domain.assert_called()
        self.mock_builder.build.assert_called_once()
        self.assertEqual(self.bot.client, self.mock_client_instance)

    def test_init_with_lark_domain(self):
        """Test initialization with Lark domain."""
        # Reset mocks
        self.mock_lark_oapi.Client.builder.reset_mock()
        self.mock_builder.reset_mock()
        
        # Setup config with Lark domain
        lark_config = MagicMock(spec=FeishuConfig)
        lark_config.FEISHU_APP_ID.value = "fake_app_id"
        lark_config.FEISHU_APP_SECRET.value = "fake_app_secret"
        lark_config.FEISHU_API_BASE.value = "https://open.larksuite.com"
        
        # Initialize bot
        bot = LarkBot(config=lark_config)
        
        # Verify domain was set correctly
        self.mock_builder.domain.assert_called_with("https://open.larksuite.com")

    def test_send_text(self):
        """Test send_text method."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.success.return_value = True
        mock_response.data.message_id = "msg_123"
        self.mock_client_instance.im.v1.message.create.return_value = mock_response

        # Call method
        receive_id = "user_1"
        receive_id_type = "open_id"
        text = "Hello World"
        self.bot.send_text(receive_id, receive_id_type, text)

        # Verify Body Builder calls
        self.mock_msg_body_builder.receive_id.assert_called_with(receive_id)
        self.mock_msg_body_builder.msg_type.assert_called_with("text")
        expected_content = json.dumps({"text": text})
        self.mock_msg_body_builder.content.assert_called_with(expected_content)
        self.mock_msg_body_builder.build.assert_called_once()

        # Verify Request Builder calls
        self.mock_msg_req_builder.receive_id_type.assert_called_with(receive_id_type)
        self.mock_msg_req_builder.request_body.assert_called_with(self.mock_msg_body)
        self.mock_msg_req_builder.build.assert_called_once()

        # Verify Client call
        self.mock_client_instance.im.v1.message.create.assert_called_with(self.mock_msg_req)

    def test_send_post(self):
        """Test send_post method."""
        mock_response = MagicMock()
        mock_response.success.return_value = True
        self.mock_client_instance.im.v1.message.create.return_value = mock_response

        receive_id = "user_2"
        receive_id_type = "user_id"
        content = {"title": "Test Post", "content": [[]]}
        self.bot.send_post(receive_id, receive_id_type, content)

        # Verify Body Builder calls
        self.mock_msg_body_builder.receive_id.assert_called_with(receive_id)
        self.mock_msg_body_builder.msg_type.assert_called_with("post")
        expected_content = json.dumps(content)
        self.mock_msg_body_builder.content.assert_called_with(expected_content)

        # Verify Client call
        self.mock_client_instance.im.v1.message.create.assert_called_with(self.mock_msg_req)

    def test_send_image(self):
        """Test send_image method."""
        mock_response = MagicMock()
        mock_response.success.return_value = True
        self.mock_client_instance.im.v1.message.create.return_value = mock_response

        receive_id = "chat_1"
        receive_id_type = "chat_id"
        image_key = "img_key_123"
        self.bot.send_image(receive_id, receive_id_type, image_key)

        # Verify Body Builder calls
        self.mock_msg_body_builder.receive_id.assert_called_with(receive_id)
        self.mock_msg_body_builder.msg_type.assert_called_with("image")
        expected_content = json.dumps({"image_key": image_key})
        self.mock_msg_body_builder.content.assert_called_with(expected_content)

        # Verify Client call
        self.mock_client_instance.im.v1.message.create.assert_called_with(self.mock_msg_req)

    def test_send_card(self):
        """Test send_card method."""
        mock_response = MagicMock()
        mock_response.success.return_value = True
        self.mock_client_instance.im.v1.message.create.return_value = mock_response

        receive_id = "open_id_1"
        receive_id_type = "open_id"
        card_content = {"config": {}, "elements": []}
        self.bot.send_card(receive_id, receive_id_type, card_content)

        # Verify Body Builder calls
        self.mock_msg_body_builder.receive_id.assert_called_with(receive_id)
        self.mock_msg_body_builder.msg_type.assert_called_with("interactive")
        expected_content = json.dumps(card_content)
        self.mock_msg_body_builder.content.assert_called_with(expected_content)

        # Verify Client call
        self.mock_client_instance.im.v1.message.create.assert_called_with(self.mock_msg_req)

    def test_send_message_object(self):
        """Test send_message method with Message object."""
        mock_response = MagicMock()
        mock_response.success.return_value = True
        self.mock_client_instance.im.v1.message.create.return_value = mock_response

        receive_id = "user_3"
        receive_id_type = "user_id"
        
        # Test TextMessage
        text_msg = TextMessage("Hello Object")
        self.bot.send_message(receive_id, receive_id_type, text_msg)

        # Verify Body Builder calls
        self.mock_msg_body_builder.receive_id.assert_called_with(receive_id)
        self.mock_msg_body_builder.msg_type.assert_called_with("text")
        self.mock_msg_body_builder.content.assert_called_with(text_msg.to_json())
        
        # Reset mocks for next sub-test
        self.mock_msg_body_builder.reset_mock()
        self.mock_client_instance.reset_mock()
        
        # Test PostMessage
        post_content = [[{"tag": "text", "text": "Post Content"}]]
        post_msg = PostMessage("Post Title", post_content)
        self.bot.send_message(receive_id, receive_id_type, post_msg)
        
        # Verify Body Builder calls
        self.mock_msg_body_builder.receive_id.assert_called_with(receive_id)
        self.mock_msg_body_builder.msg_type.assert_called_with("post")
        self.mock_msg_body_builder.content.assert_called_with(post_msg.to_json())

    def test_get_chat_info(self):
        """Test get_chat_info method."""
        mock_response = MagicMock()
        mock_response.success.return_value = True
        self.mock_client_instance.im.v1.chat.get.return_value = mock_response

        chat_id = "chat_123"
        user_id_type = "open_id"
        self.bot.get_chat_info(chat_id, user_id_type)

        # Verify Builder calls
        self.mock_chat_req_builder.chat_id.assert_called_with(chat_id)
        self.mock_chat_req_builder.user_id_type.assert_called_with(user_id_type)
        self.mock_chat_req_builder.build.assert_called_once()

        # Verify Client call
        self.mock_client_instance.im.v1.chat.get.assert_called_with(self.mock_chat_req)

    def test_get_chat_members(self):
        """Test get_chat_members method."""
        mock_response = MagicMock()
        mock_response.success.return_value = True
        self.mock_client_instance.im.v1.chat_members.get.return_value = mock_response

        chat_id = "chat_123"
        self.bot.get_chat_members(chat_id)

        # Verify Builder calls
        self.mock_members_req_builder.chat_id.assert_called_with(chat_id)
        self.mock_members_req_builder.member_id_type.assert_called_with("open_id")
        self.mock_members_req_builder.page_size.assert_called_with(20)
        self.mock_members_req_builder.build.assert_called_once()

        # Verify Client call
        self.mock_client_instance.im.v1.chat_members.get.assert_called_with(self.mock_members_req)
