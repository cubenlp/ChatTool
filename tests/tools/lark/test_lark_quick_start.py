import pytest
import os
import logging
from chattool.tools.lark.bot import LarkBot
from chattool.config.main import FeishuConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def lark_bot():
    """Fixture to provide a configured LarkBot instance."""
    config = FeishuConfig()
    if not config.FEISHU_APP_ID.value or not config.FEISHU_APP_SECRET.value or config.FEISHU_APP_ID.value == "fake_app_id":
        pytest.skip("Feishu credentials not configured in environment")
    return LarkBot(config=config)

@pytest.fixture(scope="module")
def target_user():
    """Fixture to provide the target user ID."""
    # User specified "rexwzh" as user_id
    return "rexwzh"

@pytest.fixture(scope="module")
def target_email():
    """Fixture to provide the target user email."""
    return "rexwzh@feishu.leanprover.cn"

def test_quick_start_bot_info(lark_bot):
    """
    Test getting bot info (Smoke Test).
    Ensures app_id and app_secret are valid and bot is accessible.
    """
    logger.info("Testing get_bot_info...")
    response = lark_bot.get_bot_info()
    
    if response.code != 0:
        pytest.fail(f"Failed to get bot info: {response.msg} (Code: {response.code})")
        
    import json
    data = json.loads(response.raw.content)
    bot_info = data.get("bot", {})
    
    logger.info(f"Bot Name: {bot_info.get('app_name')}")
    assert bot_info.get("activate_status") == 2, "Bot is not activated (status != 2)"

def test_quick_start_send_text(lark_bot, target_user, target_email):
    """
    Test sending a text message (Auto-reply scenario part 1: Sending).
    Based on Quick Start: https://open.feishu.cn/document/develop-robots/quick-start
    """
    logger.info(f"Testing send_text to user_id: {target_user}")
    
    # Attempt to send by user_id
    response = lark_bot.send_text(
        receive_id=target_user,
        receive_id_type="user_id",
        text="[Pytest] Hello! This is a test message from ChatTool (Quick Start Verification)."
    )
    
    if not response.success():
        logger.warning(f"Failed to send to user_id '{target_user}': {response.msg}")
        
        # Check for permission error
        if response.code == 99991672 or "contact:user.employee_id:readonly" in response.msg:
            logger.warning("Missing 'contact:user.employee_id:readonly' scope. Trying email fallback.")
            
            # Fallback to email if user_id fails due to permission
            response = lark_bot.send_text(
                receive_id=target_email,
                receive_id_type="email",
                text="[Pytest] Hello! This is a fallback test message via Email."
            )
            
            if not response.success():
                # Report "Bot ability not activated" clearly
                if response.code == 230006:
                     msg = ("\n[Error] Bot ability is not activated for this app."
                            "\nPlease go to Feishu Developer Console -> Features -> Bot and enable it."
                            "\nAlso ensure you have published a version of the app.")
                     pytest.fail(f"Failed to send via email: {response.msg}{msg}")
                else:
                    pytest.fail(f"Failed to send via email: {response.msg}")
            else:
                logger.info(f"Successfully sent text via email. Msg ID: {response.data.message_id}")
        else:
            pytest.fail(f"API call failed: {response.msg}")
    else:
        logger.info(f"Successfully sent text via user_id. Msg ID: {response.data.message_id}")
        assert response.data.message_id is not None

def test_quick_start_send_card(lark_bot, target_user, target_email):
    """
    Test sending an interactive card (Card Interaction scenario).
    """
    logger.info("Testing send_card...")
    
    # Simple card content
    card_content = {
        "config": {
            "wide_screen_mode": True
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": "[Pytest] This is a test card.\nVerify if you can see this.",
                    "tag": "lark_md"
                }
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "content": "Click Me",
                            "tag": "plain_text"
                        },
                        "type": "primary",
                        "value": {"key": "value"}
                    }
                ]
            }
        ],
        "header": {
            "title": {
                "content": "ChatTool Test Card",
                "tag": "plain_text"
            }
        }
    }

    # Attempt to send by user_id first
    response = lark_bot.send_card(
        receive_id=target_user,
        receive_id_type="user_id",
        card_content=card_content
    )

    if not response.success():
        logger.warning(f"Failed to send card to user_id '{target_user}': {response.msg}")
        
        if response.code == 99991672 or "contact:user.employee_id:readonly" in response.msg:
            logger.warning("Missing permission for user_id. Trying email fallback.")
             # Fallback to email
            response = lark_bot.send_card(
                receive_id=target_email,
                receive_id_type="email",
                card_content=card_content
            )
            
            if not response.success():
                if response.code == 230006:
                     msg = ("\n[Error] Bot ability is not activated for this app."
                            "\nPlease go to Feishu Developer Console -> Features -> Bot and enable it."
                            "\nAlso ensure you have published a version of the app.")
                     pytest.fail(f"Failed to send card via email: {response.msg}{msg}")
                else:
                     pytest.fail(f"Failed to send card via email: {response.msg}")
            else:
                 logger.info(f"Successfully sent card via email. Msg ID: {response.data.message_id}")
        else:
             pytest.fail(f"API call failed: {response.msg}")
    else:
        logger.info(f"Successfully sent card via user_id. Msg ID: {response.data.message_id}")
        assert response.data.message_id is not None
