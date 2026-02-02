import sqlite3
import json
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

@dataclass
class KBMessage:
    id: int
    stream: str
    topic: str
    sender: str
    content: str
    timestamp: float
    raw_data: str

class KBStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Messages Table with FTS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                stream TEXT,
                topic TEXT,
                sender TEXT,
                content TEXT,
                timestamp REAL,
                raw_data TEXT
            )
        ''')
        
        # FTS Virtual Table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                content, 
                topic, 
                stream, 
                sender, 
                content='messages', 
                content_rowid='id'
            )
        ''')

        # Sync State Table (stream -> last_message_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_state (
                stream TEXT PRIMARY KEY,
                last_message_id INTEGER DEFAULT 0
            )
        ''')
        
        # Config Table (key -> value)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Notes/Knowledge Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT, -- 'message' or 'topic'
                target_id TEXT, -- message_id or topic_name
                content TEXT,
                created_at REAL
            )
        ''')

        conn.commit()
        conn.close()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    # --- Config ---
    def set_config(self, key: str, value: str):
        conn = self._get_conn()
        conn.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()

    def get_config(self, key: str) -> Optional[str]:
        conn = self._get_conn()
        cursor = conn.execute('SELECT value FROM config WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    # --- Sync State ---
    def get_last_message_id(self, stream: str) -> int:
        conn = self._get_conn()
        cursor = conn.execute('SELECT last_message_id FROM sync_state WHERE stream = ?', (stream,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def update_last_message_id(self, stream: str, message_id: int):
        conn = self._get_conn()
        conn.execute('INSERT OR REPLACE INTO sync_state (stream, last_message_id) VALUES (?, ?)', (stream, message_id))
        conn.commit()
        conn.close()

    # --- Messages ---
    def add_messages(self, messages: List[Dict]):
        if not messages:
            return
        conn = self._get_conn()
        cursor = conn.cursor()
        
        for msg in messages:
            # Zulip message structure: id, content, sender_full_name, timestamp, etc.
            # We assume stream messages.
            # If sender is dict, extract full_name or email
            sender = msg.get('sender_full_name', 'Unknown')
            if not sender and 'sender_email' in msg:
                sender = msg['sender_email']
                
            stream = msg.get('display_recipient', 'unknown')
            if isinstance(stream, list): # Private message recipient list
                stream = "private" 
                
            topic = msg.get('subject', 'general') # 'subject' is topic in API
            
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO messages (id, stream, topic, sender, content, timestamp, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    msg['id'],
                    stream,
                    topic,
                    sender,
                    msg['content'],
                    msg.get('timestamp', time.time()),
                    json.dumps(msg)
                ))
                
                # Update FTS index (triggers are better but manual insert is simple for now)
                cursor.execute('''
                    INSERT INTO messages_fts (rowid, content, topic, stream, sender)
                    VALUES (?, ?, ?, ?, ?)
                ''', (msg['id'], msg['content'], topic, stream, sender))
                
            except Exception as e:
                print(f"Error saving message {msg.get('id')}: {e}")

        conn.commit()
        conn.close()

    def search_messages(self, query: str) -> List[KBMessage]:
        conn = self._get_conn()
        cursor = conn.execute('''
            SELECT id, stream, topic, sender, content, timestamp, raw_data 
            FROM messages 
            WHERE id IN (SELECT rowid FROM messages_fts WHERE messages_fts MATCH ? ORDER BY rank)
            LIMIT 50
        ''', (query,))
        
        results = []
        for row in cursor.fetchall():
            results.append(KBMessage(*row))
        conn.close()
        return results

    def get_messages_by_topic(self, stream: str, topic: str, limit: int = 100) -> List[KBMessage]:
        conn = self._get_conn()
        cursor = conn.execute('''
            SELECT id, stream, topic, sender, content, timestamp, raw_data 
            FROM messages 
            WHERE stream = ? AND topic = ?
            ORDER BY id ASC
            LIMIT ?
        ''', (stream, topic, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append(KBMessage(*row))
        conn.close()
        return results
    
    def get_all_topics(self, stream: Optional[str] = None) -> List[Tuple[str, str, int]]:
        """Returns list of (stream, topic, count)"""
        conn = self._get_conn()
        if stream:
            cursor = conn.execute('''
                SELECT stream, topic, COUNT(*) as cnt 
                FROM messages 
                WHERE stream = ?
                GROUP BY stream, topic
                ORDER BY cnt DESC
            ''', (stream,))
        else:
            cursor = conn.execute('''
                SELECT stream, topic, COUNT(*) as cnt 
                FROM messages 
                GROUP BY stream, topic
                ORDER BY cnt DESC
            ''')
        
        results = cursor.fetchall()
        conn.close()
        return results
