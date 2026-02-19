import json
from typing import List, Optional
from urllib.parse import urlparse

from chattool.const import CHATTOOL_CACHE_DIR
from chattool.application.kb.storage import KBStorage, KBMessage
from chattool.application.kb.ingest import ZulipIngester
from chattool.tools.zulip.client import ZulipClient
from chattool.config import ZulipConfig

# Default KB directory inside the cache, organized by site
DEFAULT_KB_CACHE_DIR = CHATTOOL_CACHE_DIR / "kb"

class KBManager:
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the Knowledge Base Manager.
        
        Args:
            name: Workspace name. If None, defaults to the Zulip site hostname.
                  The database will be stored in CHATTOOL_CACHE_DIR/kb/<site>/<name>.db
        """
        self.client = ZulipClient() # For reposting and config access
        
        # Determine site hostname for folder organization
        site_url = ZulipConfig.ZULIP_SITE.value
        if site_url:
            try:
                self.site_host = urlparse(site_url).hostname or "unknown_site"
            except:
                self.site_host = "unknown_site"
        else:
            self.site_host = "default_site"
            
        # Determine workspace name
        self.name = name or self.site_host
        
        # Construct path: ~/.cache/chattool/kb/<site_host>/<name>.db
        self.kb_dir = DEFAULT_KB_CACHE_DIR / self.site_host
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.kb_dir / f"{self.name}.db"
        
        # Initialize storage
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

    def sync(self, fetch_newest: bool = False, limit: int = 1000):
        """Sync all tracked streams."""
        self.ingester.sync_all_tracked_streams(fetch_newest=fetch_newest, limit=limit)

    def list_topics(self, stream: Optional[str] = None):
        """List topics with message counts."""
        return self.storage.get_all_topics(stream)

    def get_messages(self, stream: str, topic: str, limit: int = 100) -> List[KBMessage]:
        return self.storage.get_messages_by_topic(stream, topic, limit)

    def search(self, query: str) -> List[KBMessage]:
        return self.storage.search_messages(query)

    def process_topic(self, stream: str, topic: str, processor_func) -> str:
        """
        Process messages in a topic and return a result.
        """
        messages = self.get_messages(stream, topic, limit=1000)
        if not messages:
            return "No content found."
        
        # Simple concatenation for now, can be replaced by LLM summary
        content = "\n".join([f"{m.sender}: {m.content}" for m in messages])
        return processor_func(content)

    def repost_knowledge(self, to_stream: str, to_topic: str, content: str):
        """Post processed knowledge back to Zulip."""
        self.client.send_message(
            type="stream",
            to=to_stream,
            topic=to_topic,
            content=content
        )

    def export_topics(self, output_file: str):
        """Export topic list to a file."""
        topics = self.list_topics()
        with open(output_file, 'w') as f:
            f.write("Stream,Topic,Count\n")
            for s, t, c in topics:
                f.write(f"{s},{t},{c}\n")
    
    def export_messages(self, stream: str, topic: str, output_file: str):
        """Export messages of a topic to a file."""
        messages = self.get_messages(stream, topic, limit=1000)
        with open(output_file, 'w') as f:
            for msg in messages:
                f.write(f"--- {msg.sender} at {msg.timestamp} ---\n")
                f.write(f"{msg.content}\n\n")
