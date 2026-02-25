import pytest
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.lark
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
