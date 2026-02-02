import os
import json
from pathlib import Path
from typing import List, Optional
from chattool.application.kb.storage import KBStorage, KBMessage
from chattool.application.kb.ingest import ZulipIngester

DEFAULT_KB_DIR = Path.home() / ".chattool" / "kb"

class KBManager:
    def __init__(self, name: str):
        self.name = name
        self.kb_dir = DEFAULT_KB_DIR
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.kb_dir / f"{name}.db"
        self.storage = KBStorage(str(self.db_path))
        self.ingester = ZulipIngester(self.storage)

    def track_stream(self, stream_name: str):
        """Add a stream to the tracking list."""
        current = self.storage.get_config("tracked_streams")
        streams = []
        if current:
            try:
                streams = json.loads(current)
            except:
                streams = [s.strip() for s in current.split(',') if s.strip()]
        
        if stream_name not in streams:
            streams.append(stream_name)
            self.storage.set_config("tracked_streams", json.dumps(streams))
            print(f"Stream '{stream_name}' added to workspace '{self.name}'.")
        else:
            print(f"Stream '{stream_name}' is already tracked.")

    def untrack_stream(self, stream_name: str):
        """Remove a stream from the tracking list."""
        current = self.storage.get_config("tracked_streams")
        if not current:
            return
            
        try:
            streams = json.loads(current)
        except:
            streams = [s.strip() for s in current.split(',') if s.strip()]
            
        if stream_name in streams:
            streams.remove(stream_name)
            self.storage.set_config("tracked_streams", json.dumps(streams))
            print(f"Stream '{stream_name}' removed from workspace '{self.name}'.")

    def list_tracked_streams(self) -> List[str]:
        current = self.storage.get_config("tracked_streams")
        if not current:
            return []
        try:
            return json.loads(current)
        except:
            return [s.strip() for s in current.split(',') if s.strip()]

    def sync(self):
        """Sync all tracked streams."""
        self.ingester.sync_all_tracked_streams()

    def list_topics(self, stream: Optional[str] = None):
        """List topics with message counts."""
        return self.storage.get_all_topics(stream)

    def get_messages(self, stream: str, topic: str, limit: int = 100) -> List[KBMessage]:
        return self.storage.get_messages_by_topic(stream, topic, limit)

    def search(self, query: str) -> List[KBMessage]:
        return self.storage.search_messages(query)
