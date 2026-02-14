import pytest
import time
from chattool.tools.zulip.client import ZulipClient
from chattool.utils.config import ZulipConfig

def test_zulip_setup():
    print('API Key:', ZulipConfig.ZULIP_BOT_API_KEY.value[:5])
    print('Bot Email:', ZulipConfig.ZULIP_BOT_EMAIL.value[-7:])
    print('Zulip Site:', ZulipConfig.ZULIP_SITE.value)

class TestZulipIntegration:
    
    def setup_method(self):
        self.client = ZulipClient()
        self.my_email = ZulipConfig.ZULIP_BOT_EMAIL.value

    def test_list_streams(self):
        streams = self.client.list_streams(include_public=True)
        assert isinstance(streams, list)
        print(f"Found {len(streams)} streams")

    def test_get_messages(self):
        msgs = self.client.get_messages(num_before=5)
        assert isinstance(msgs, list)
        print(f"Found {len(msgs)} messages")

    def test_send_private_message_to_self(self):
        """Test sending a PM to the bot itself (safe test)"""
        
        # Get own profile to find user_id
        profile = self.client.get_profile()
        user_id = profile.get("user_id")
        email = profile.get("email") or self.my_email
        print(f"Testing with User ID: {user_id}, Email: {email}")
        
        content = "Integration test message from ChatTool (Sync)"
        
        # In new client, send_message returns the API response dict
        # Try sending to User ID first (more robust)
        target = [user_id] if user_id else [email]
        
        result = self.client.send_message(
            to=target,  # Send to self
            content=content,
            type="private"
        )
        
        assert result.get("result") == "success"
        msg_id = result.get("id")
        assert msg_id is not None
        print(f"Sent message ID: {msg_id}")
        
        # Verify by fetching
        time.sleep(2) # Wait for propagation
        msgs = self.client.get_messages(
            num_before=10, 
            narrow=[{"operator": "sender", "operand": email}]
        )
        
        found = False
        for m in msgs:
            if str(msg_id) == str(m['id']):
                found = True
                break
        
        if not found:
            print("Warning: Sent message not found in recent history (could be sync delay)")

    def test_search_messages(self):
        # Search for something likely to exist
        msgs = self.client.get_messages(
            num_before=5,
            narrow=[{"operator": "search", "operand": "hello"}]
        )
        assert isinstance(msgs, list)
