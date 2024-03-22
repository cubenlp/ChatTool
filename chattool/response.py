# Response class for Chattool

from typing import Dict
from .tokencalc import findcost

class Resp():
    
    def __init__(self, response:Dict) -> None:
        self.response = response
    
    def is_valid(self):
        """Check if the response is an error"""
        return 'error' not in self.response
    
    def cost(self):
        """Calculate the cost of the response"""
        return findcost(self.model, self.prompt_tokens, self.completion_tokens)
    
    def __repr__(self) -> str:
        return "<Resp with finished reason: " + self.finish_reason + ">"
    
    def __str__(self) -> str:
        return self.content

    @property
    def id(self):
        return self.response['id']
    
    @property
    def model(self):
        return self.response['model']
    
    @property
    def created(self):
        return self.response['created']
    
    @property
    def usage(self):
        """Token usage"""
        return self.response['usage']
    
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
        return self.response['choices'][0]['message']
    
    @property
    def content(self):
        """Content of the response"""
        return self.message['content']
    
    @property
    def function_call(self):
        """Function call"""
        return self.message.get('function_call')
    
    @property
    def delta(self):
        """Delta"""
        return self.response['choices'][0]['delta']
    
    @property
    def delta_content(self):
        """Content of stream response"""
        return self.delta['content']
    
    @property
    def object(self):
        return self.response['object']
    
    @property
    def error(self):
        """Error"""
        return self.response['error']
    
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
        return self.response['choices'][0].get('finish_reason')
