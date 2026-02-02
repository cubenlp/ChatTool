from typing import List, Dict, Optional
import time
from chattool.tools.zulip.client import ZulipClient
from chattool.application.kb.storage import KBStorage
from chattool.utils import setup_logger

logger = setup_logger("zulip_kb_ingest")

class ZulipIngester:
    def __init__(self, storage: KBStorage):
        self.client = ZulipClient()
        self.storage = storage

    def sync_stream(self, stream_name: str, batch_size: int = 100):
        """
        Incrementally sync messages from a stream.
        """
        last_id = self.storage.get_last_message_id(stream_name)
        logger.info(f"Syncing stream '{stream_name}' starting from ID {last_id}...")
        
        while True:
            # Zulip API: anchor is the message ID to start from. 
            # num_before=0, num_after=batch_size means fetch messages AFTER anchor.
            # But anchor itself is included if we don't handle it carefully.
            # Usually we set anchor to last_id and use num_after.
            
            # Note: client.get_messages uses 'anchor', 'num_before', 'num_after'
            messages = self.client.get_messages(
                anchor=last_id,
                num_before=0,
                num_after=batch_size,
                narrow=[{"operator": "stream", "operand": stream_name}]
            )
            
            if not messages:
                logger.info(f"No more messages found for stream '{stream_name}'.")
                break
                
            # Filter out messages we've already seen (anchor is included in response usually)
            new_messages = [m for m in messages if m['id'] > last_id]
            
            if not new_messages:
                logger.info("No new messages (caught up).")
                break
                
            logger.info(f"Fetched {len(new_messages)} new messages.")
            
            # Save to storage
            self.storage.add_messages(new_messages)
            
            # Update last_id
            max_id = max(m['id'] for m in new_messages)
            last_id = max_id
            self.storage.update_last_message_id(stream_name, last_id)
            
            # Rate limit politeness
            time.sleep(0.2)

    def sync_all_tracked_streams(self):
        """
        Sync all streams configured in the workspace.
        """
        # Load tracked streams from config
        # We assume config stores a comma-separated list or JSON list of streams
        tracked_str = self.storage.get_config("tracked_streams")
        if not tracked_str:
            logger.warning("No tracked streams configured. Use 'kb track <stream>' first.")
            return

        import json
        try:
            streams = json.loads(tracked_str)
        except:
            streams = [s.strip() for s in tracked_str.split(',') if s.strip()]
            
        for stream in streams:
            self.sync_stream(stream)
