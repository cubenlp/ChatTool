# The object that stores the chat log

from typing import List, Dict, Union
import openai_api_call
from .response import Resp
import openai

class Chat():
    def __init__(self, msg:Union[List[Dict], None, str]=None) -> None:
        if msg is None:
            self._chat_log = []
        elif isinstance(msg, str):
            self._chat_log = openai_api_call.default_prompt(msg)
        elif isinstance(msg, list):
            self._chat_log = msg
        else:
            raise ValueError("msg should be a list of dict, a string or None")
    
    def getresponse( self
                   , max_requests:int=1
                   , strip:bool=True
                   , update:bool = True
                   , model:str = "gpt-3.5-turbo"
                   , **options)->Resp:
        """Get the API response

        Args:
            max_requests (int, optional): maximum number of requests to make. Defaults to 1.
            strip (bool, optional): whether to strip the prompt message. Defaults to True.
            update (bool, optional): whether to update the chat log. Defaults to True.
            model (str, optional): model to use. Defaults to "gpt-3.5-turbo".
            **options : options inherited from the `openai.ChatCompletion.create` function.

        Returns:
            Resp: API response
        """
        assert openai.api_key is not None, "API key is not set!"

        # initialize prompt message
        msg = self.chat_log
        
        # default options
        if not len(options):
            options = {}
        # make request
        resp = None
        numoftries = 0
        while max_requests:
            try:
                response = openai.ChatCompletion.create(
                    messages=msg, model=model,
                    **options)
                resp = Resp(response, strip=strip)
            except:
                max_requests -= 1
                numoftries += 1
                print(f"API call failed! Try again ({numoftries})")
                continue
            break
        else:
            raise Exception("API call failed!\nYou can try to update the API key"
                            + ", increase `max_requests` or set proxy.")
        if update: # update the chat log
            self.assistant(resp.content)
        return resp

    def add(self, role:str, msg:str):
        assert role in ['user', 'assistant', 'system'], "role should be 'user', 'assistant' or 'system'"
        self._chat_log.append({"role": role, "content": msg})
        return self

    def user(self, msg):
        """User message"""
        return self.add('user', msg)
    
    def assistant(self, msg):
        """Assistant message"""
        return self.add('assistant', msg)
    
    def system(self, msg):
        """System message"""
        return self.add('system', msg)
    
    def clear(self):
        """Clear the chat log"""
        self._chat_log = []
    
    def copy(self):
        """Copy the chat log"""
        return Chat(self._chat_log.copy())
    
    def print_log(self, sep: Union[str, None]=None):
        if sep is None:
            sep = '\n' + '-'*15 + '\n'
        for d in self._chat_log:
            print(sep, d['role'], sep, d['content'])
    
    @property
    def chat_log(self):
        """Chat history"""
        return self._chat_log
    
    def pop(self):
        """Pop the last message"""
        return self._chat_log.pop()
    
    def __len__(self):
        """Length of the chat log"""
        return len(self._chat_log)
    
    def __repr__(self) -> str:
        return f"<Chat with {len(self)} messages>"
    
    def __str__(self) -> str:
        return f"{self.history}"

