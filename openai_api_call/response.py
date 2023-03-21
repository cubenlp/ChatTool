# Response class for OpenAI API call

from typing import List, Dict, Union

class Resp():
    
    def __init__(self, response:Union[List[Dict], None]=None) -> None:
        self.response = response
        self._request_msg = None

    def chat_log(self):
        """Chat history"""
        assert self._request_msg is not None, "Request message is not set!"
        ai_resp = {"role": "assistant", "content": self.content}
        return self._request_msg + [ai_resp]
    
    def next_prompt(self, msg):
        """next prompt for the next API call"""
        prompt = {"role": "user", "content": msg}
        return self.chat_log() + [prompt]

    def _strip_content(self):
        """Strip the content"""
        self.response['choices'][0]['message']['content'] = \
            self.response['choices'][0]['message']['content'].strip()
    
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

