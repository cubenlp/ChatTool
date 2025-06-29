from typing import Optional, List, Dict, Union
from chattool.core.config import Config, OpenAIConfig
from chattool.core.request import OpenAIClient, HTTPClient

class Chat(OpenAIClient):
    def __init__(self, config: Optional[OpenAIConfig] = None, chat_log: Optional[List[Dict]] = None):
        if chat_log is None:
            chat_log = []
        self.chat_log = chat_log
        super().__init__(config)
    
    def add(self, role:str, **kwargs):
        """Add a message to the chat log"""
        assert role in ['user', 'assistant', 'system', 'tool', 'function'],\
            f"role should be one of ['user', 'assistant', 'system', 'tool'], but got {role}"
        self.chat_log.append({'role':role, **kwargs})
        return self

    def user(self, content: Union[List, str]):
        """User message"""
        return self.add('user', content=content)
    
    def assistant(self, content:Optional[str]=None):
        """Assistant message"""
        return self.add('assistant', content=content)
    
    def system(self, content:str):
        """System message"""
        return self.add('system', content=content)
    
    def chat_completion(self, messages:Optional[List[dict]]=None, model = None, temperature = None, top_p = None, max_tokens = None, stream = False, **kwargs):
        """Chat completion"""
        if messages is None:
            messages = self.chat_log
        return super().chat_completion(messages, model, temperature, top_p, max_tokens, stream, **kwargs)
