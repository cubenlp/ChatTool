# Response class for OpenAI API call

from typing import Dict

class Resp():
    
    def __init__(self, response:Dict, strip:bool=True) -> None:
        self.response = response
        if strip and self.is_valid(): self._strip_content()
    
    def _strip_content(self):
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
        return self.response['id']
    
    @property
    def model(self):
        return self.response['model']
    
    @property
    def created(self):
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

