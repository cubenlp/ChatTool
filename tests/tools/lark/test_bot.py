import sys
import unittest
import json
from unittest.mock import MagicMock, patch

# Mock lark_oapi before importing LarkBot
mock_lark_oapi = MagicMock()
sys.modules["lark_oapi"] = mock_lark_oapi
sys.modules["lark_oapi.api"] = MagicMock()
sys.modules["lark_oapi.api.im"] = MagicMock()
sys.modules["lark_oapi.api.im.v1"] = MagicMock()

# Mock the specific classes imported by LarkBot
mock_im_v1 = sys.modules["lark_oapi.api.im.v1"]
mock_im_v1.CreateMessageRequest = MagicMock()
mock_im_v1.CreateMessageRequestBody = MagicMock()
mock_im_v1.GetChatRequest = MagicMock()
mock_im_v1.GetChatMembersRequest = MagicMock()

# Import LarkBot
from chattool.tools.lark.bot import LarkBot
from chattool.config.main import FeishuConfig

class TestLarkBot(unittest.TestCase):
    def setUp(self):
        # Mock Config
        self.mock_config = MagicMock(spec=FeishuConfig)
        self.mock_config.FEISHU_APP_ID.value = "fake_app_id"
        self.mock_config.FEISHU_APP_SECRET.value = "fake_app_secret"
        
        # Reset the mock for lark_oapi.Client
        mock_lark_oapi.Client.reset_mock()
        
        # Setup the builder chain mock for Client
        self.mock_builder = MagicMock()
        self.mock_client_instance = MagicMock()
        
        mock_lark_oapi.Client.builder.return_value = self.mock_builder
        self.mock_builder.app_id.return_value = self.mock_builder
        self.mock_builder.app_secret.return_value = self.mock_builder
        self.mock_builder.log_level.return_value = self.mock_builder
        self.mock_builder.build.return_value = self.mock_client_instance
        
        # Setup mocks for Request Builders
        self.setup_request_mocks()

        self.bot = LarkBot(config=self.mock_config)

    def setup_request_mocks(self):
        # CreateMessageRequestBody
        self.mock_msg_body_builder = MagicMock()
        self.mock_msg_body = MagicMock()
        mock_im_v1.CreateMessageRequestBody.builder.return_value = self.mock_msg_body_builder
        self.mock_msg_body_builder.receive_id.return_value = self.mock_msg_body_builder
        self.mock_msg_body_builder.msg_type.return_value = self.mock_msg_body_builder
        self.mock_msg_body_builder.content.return_value = self.mock_msg_body_builder
        self.mock_msg_body_builder.build.return_value = self.mock_msg_body

        # CreateMessageRequest
        self.mock_msg_req_builder = MagicMock()
        self.mock_msg_req = MagicMock()
        mock_im_v1.CreateMessageRequest.builder.return_value = self.mock_msg_req_builder
        self.mock_msg_req_builder.receive_id_type.return_value = self.mock_msg_req_builder
        self.mock_msg_req_builder.request_body.return_value = self.mock_msg_req_builder
        self.mock_msg_req_builder.build.return_value = self.mock_msg_req

        # GetChatRequest
        self.mock_chat_req_builder = MagicMock()
        self.mock_chat_req = MagicMock()
        mock_im_v1.GetChatRequest.builder.return_value = self.mock_chat_req_builder
        self.mock_chat_req_builder.chat_id.return_value = self.mock_chat_req_builder
        self.mock_chat_req_builder.user_id_type.return_value = self.mock_chat_req_builder
        self.mock_chat_req_builder.build.return_value = self.mock_chat_req

        # GetChatMembersRequest
        self.mock_members_req_builder = MagicMock()
        self.mock_members_req = MagicMock()
        mock_im_v1.GetChatMembersRequest.builder.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.chat_id.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.member_id_type.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.page_size.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.page_token.return_value = self.mock_members_req_builder
        self.mock_members_req_builder.build.return_value = self.mock_members_req

    def test_init(self):
        """Test initialization of LarkBot."""
        mock_lark_oapi.Client.builder.assert_called_once()
        self.mock_builder.app_id.assert_called_with("fake_app_id")
        self.mock_builder.app_secret.assert_called_with("fake_app_secret")
        self.mock_builder.log_level.assert_called_with(mock_lark_oapi.LogLevel.DEBUG)
        # Verify domain is called because mock config returns a truthy mock for FEISHU_API_BASE
        self.mock_builder.domain.assert_called()
        self.mock_builder.build.assert_called_once()
        self.assertEqual(self.bot.client, self.mock_client_instance)

    def test_init_with_lark_domain(self):
        """Test initialization with Lark domain."""
        # Reset mocks
        mock_lark_oapi.Client.builder.reset_mock()
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

    def test_get_chat_info(self):
        """Test get_chat_info method."""
        mock_response = MagicMock()
        mock_response.success.return_value = True
        self.mock_client_instance.im.v1.chat.get.return_value = mock_response

        chat_id = "chat_123"
        user_id_type = "open_id"
        self.bot.get_chat_info(chat_id, user_id_type)

        # Verify Request Builder calls
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
        member_id_type = "user_id"
        page_size = 50
        page_token = "token_123"
        self.bot.get_chat_members(chat_id, member_id_type, page_size, page_token)

        # Verify Request Builder calls
        self.mock_members_req_builder.chat_id.assert_called_with(chat_id)
        self.mock_members_req_builder.member_id_type.assert_called_with(member_id_type)
        self.mock_members_req_builder.page_size.assert_called_with(page_size)
        self.mock_members_req_builder.page_token.assert_called_with(page_token)
        self.mock_members_req_builder.build.assert_called_once()

        # Verify Client call
        self.mock_client_instance.im.v1.chat_members.get.assert_called_with(self.mock_members_req)

if __name__ == "__main__":
    unittest.main()
