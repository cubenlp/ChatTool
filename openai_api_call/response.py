# Response class for OpenAI API call

from typing import List, Dict, Union
from .chat import Chat

class Resp():
    
    def __init__(self, response:Dict, msg:Union[List[Dict], None, str, Chat]=None) -> None:
        """
        Args:
            response (Dict): response from OpenAI API call
            msg (List[Dict], optional): prompt message. Defaults to None.
        """
        self.response = response
        self._oldchat = msg if isinstance(msg, Chat) else Chat(msg)
        self._chat = None
    
    @property
    def chat(self):
        """The chat object"""
        if self._chat is None:
            self._chat = self._oldchat.copy().assistant(self.content)
        return self._chat
 
    def strip_content(self):
        """Strip the content"""
        self.response['choices'][0]['message']['content'] = \
            self.response['choices'][0]['message']['content'].strip()

    def __repr__(self) -> str:
        return f"`Resp`: {self.content}"
    
    def __str__(self) -> str:
        return self.content

    @property
    def total_tokens(self):
        """Total number of tokens"""
        return self.response['usage']['total_tokens']
    
    @property
    def prompt_tokens(self):
        """Number of tokens in the prompt"""
        return self.response['usage']['prompt_tokens']
    
    @property
    def completion_tokens(self):
        """Number of tokens of the response"""
        return self.response['usage']['completion_tokens']
    
    @property
    def content(self):
        """Content of the response"""
        return self.response['choices'][0]['message']['content']
    
    @property
    def id(self):
        """ID of the response"""
        return self.response['id']
    
    @property
    def model(self):
        """Model used for the response"""
        return self.response['model']
    
    @property
    def created(self):
        """Time of the response"""
        return self.response['created']
    
    def is_valid(self):
        """Check if the response is an error"""
        return 'error' not in self.response
    
    @property
    def error_message(self):
        """Error message"""
        return self.response['error']['message']
    
    @property
    def error_type(self):
        """Error type"""
        return self.response['error']['type']
    
    @property
    def error_param(self):
        """Error parameter"""
        return self.response['error']['param']
    
    @property
    def error_code(self):
        """Error code"""
        return self.response['error']['code']