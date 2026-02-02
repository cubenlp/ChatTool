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

    def sync_stream(self, stream_name: str, batch_size: int = 100, fetch_newest: bool = False, limit: int = 1000):
        """
        Sync messages from a stream.
        
        Args:
            stream_name: The name of the stream to sync.
            batch_size: Number of messages to fetch per API call.
            fetch_newest: If True, fetches only the latest `limit` messages (reverse chronological) 
                          instead of incremental sync from last known ID.
            limit: Maximum number of messages to fetch when fetch_newest is True.
        """
        if fetch_newest:
            logger.info(f"Syncing latest {limit} messages from stream '{stream_name}'...")
            # Fetch newest messages (anchor="newest", num_before=limit)
            # We fetch in one go or batches if limit is large? 
            # get_messages supports num_before. Let's use that directly for "latest snapshot" mode.
            
            # Note: num_before can be large, but API might cap it. Zulip API usually handles up to 5000.
            # We'll try to fetch `limit` messages before "newest".
            messages = self.client.get_messages(
                anchor="newest",
                num_before=limit,
                num_after=0,
                narrow=[{"operator": "stream", "operand": stream_name}]
            )
            
            if messages:
                logger.info(f"Fetched {len(messages)} recent messages.")
                self.storage.add_messages(messages)
                
                # Update last_id to the max found, so subsequent incremental syncs work from there
                max_id = max(m['id'] for m in messages)
                current_last_id = self.storage.get_last_message_id(stream_name)
                if max_id > current_last_id:
                    self.storage.update_last_message_id(stream_name, max_id)
            else:
                logger.info("No messages found.")
            return

        # --- Incremental Sync Logic ---
        last_id = self.storage.get_last_message_id(stream_name)
        logger.info(f"Syncing stream '{stream_name}' starting from ID {last_id}...")
        
        total_fetched = 0
        while True:
            # Check safety limit for incremental sync to avoid infinite loops in demo
            if total_fetched >= limit:
                logger.info(f"Hit sync limit of {limit} messages.")
                break

            messages = self.client.get_messages(
                anchor=last_id,
                num_before=0,
                num_after=batch_size,
                narrow=[{"operator": "stream", "operand": stream_name}]
            )
            
            if not messages:
                logger.info(f"No more messages found for stream '{stream_name}'.")
                break
                
            # Filter out messages we've already seen
            new_messages = [m for m in messages if m['id'] > last_id]
            
            if not new_messages:
                logger.info("No new messages (caught up).")
                break
                
            count = len(new_messages)
            total_fetched += count
            logger.info(f"Fetched {count} new messages (Total: {total_fetched}).")
            
            # Save to storage
            self.storage.add_messages(new_messages)
            
            # Update last_id
            max_id = max(m['id'] for m in new_messages)
            last_id = max_id
            self.storage.update_last_message_id(stream_name, last_id)
            
            # Rate limit politeness
            time.sleep(0.2)

    def sync_all_tracked_streams(self, fetch_newest: bool = False, limit: int = 1000):
        """
        Sync all streams configured in the workspace.
        """
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
            self.sync_stream(stream, fetch_newest=fetch_newest, limit=limit)
