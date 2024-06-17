# Response class for Chattool

from typing import Dict, Any, Union
from .tokencalc import findcost
import chattool

class Resp():
    
    def __init__(self, response:Union[Dict, Any]) -> None:
        if isinstance(response, Dict):
            self.response = response
            self._raw_response = None
        else:
            self._raw_response = response
            self.response = response.json()
        
    def get_curl(self):
        """Convert the response to a cURL command"""
        if self._raw_response is None:
            return "No cURL command available"
        return chattool.resp2curl(self._raw_response)
    
    def print_curl(self):
        """Print the cURL command"""
        print(self.get_curl())
    
    def is_valid(self):
        """Check if the response is an error"""
        return 'error' not in self.response
    
    def cost(self):
        """Calculate the cost of the response(Deprecated)"""
        return findcost(self.model, self.prompt_tokens, self.completion_tokens)

    @property
    def id(self):
        return self['id']
    
    @property
    def model(self):
        return self['model']
    
    @property
    def created(self):
        return self['created']
    
    @property
    def usage(self):
        """Token usage"""
        return self['usage']
    
    @property
    def total_tokens(self):
        """Total number of tokens"""
        return self.usage['total_tokens']
    
    @property
    def prompt_tokens(self):
        """Number of tokens in the prompt"""
        return self.usage['prompt_tokens']
    
    @property
    def completion_tokens(self):
        """Number of tokens of the response"""
        return self.usage['completion_tokens']
    
    @property
    def message(self):
        """Message"""
        return self['choices'][0]['message']
    
    @property
    def content(self):
        """Content of the response"""
        return self.message['content']
    
    @property
    def function_call(self):
        """Function call"""
        return self.message.get('function_call')
    
    @property
    def tool_calls(self):
        """Tool calls"""
        return self.message.get('tool_calls')
    
    @property
    def delta(self):
        """Delta"""
        return self['choices'][0]['delta']
    
    @property
    def delta_content(self):
        """Content of stream response"""
        return self.delta['content']
    
    @property
    def object(self):
        return self['object']
    
    @property
    def error(self):
        """Error"""
        return self['error']
    
    @property
    def error_message(self):
        """Error message"""
        return self.error['message']
    
    @property
    def error_type(self):
        """Error type"""
        return self.error['type']
    
    @property
    def error_param(self):
        """Error parameter"""
        return self.error['param']
    
    @property
    def error_code(self):
        """Error code"""
        return self.error['code']

    @property
    def finish_reason(self):
        """Finish reason"""
        return self['choices'][0].get('finish_reason')

    def __repr__(self) -> str:
        return "<Resp with finished reason: " + self.finish_reason + ">"
    
    def __str__(self) -> str:
        return self.content
    
    def __getitem__(self, key):
        return self.response[key]
    
    def __contains__(self, key):
        return key in self.response