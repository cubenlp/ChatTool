# The object that stores the chat log

from typing import List, Dict, Union
import openai_api_call
from .response import Resp, num_tokens_from_messages
from .request import chat_completion, valid_models
import time, random
import json

class Chat():
    def __init__( self
                , msg:Union[List[Dict], None, str]=None
                , api_key:Union[None, str]=None
                , chat_url:Union[None, str]=None) -> None:
        """Initialize the chat log

        Args:
            msg (Union[List[Dict], None, str], optional): chat log. Defaults to None.
            api_key (Union[None, str], optional): API key. Defaults to None.
            chat_url (Union[None, str], optional): base url. Defaults to None. Example: "https://api.openai.com/v1/chat/completions"
        
        Raises:
            ValueError: msg should be a list of dict, a string or None
        """
        if msg is None:
            self._chat_log = []
        elif isinstance(msg, str):
            if openai_api_call.default_prompt is None:
                self._chat_log = [{"role": "user", "content": msg}]
            else:
                self._chat_log = openai_api_call.default_prompt(msg)
        elif isinstance(msg, list):
            self._chat_log = msg.copy() # avoid changing the original list
        else:
            raise ValueError("msg should be a list of dict, a string or None")
        self._api_key = openai_api_call.api_key if api_key is None else api_key
        self._chat_url = chat_url
        self._model = 'gpt-3.5-turbo'
    
    def prompt_token(self, model:str="gpt-3.5-turbo-0613"):
        """Get the prompt token for the model

        Args:
            model (str): model to use

        Returns:
            str: prompt token
        """
        return num_tokens_from_messages(self.chat_log, model=model)

    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self, model:str):
        # assert model.startswith('gpt-'), f'unsupported model {model}'
        self._model = model

    @property
    def api_key(self):
        """Get API key"""
        return self._api_key
    
    @property
    def chat_url(self):
        """Get base url"""
        return self._chat_url
    
    @api_key.setter
    def api_key(self, api_key:str):
        """Set API key"""
        self._api_key = api_key
    
    @chat_url.setter
    def chat_url(self, chat_url:str):
        """Set base url"""
        self._chat_url = chat_url

    @property
    def chat_log(self):
        """Chat history"""
        return self._chat_log
    
    def getresponse( self
                   , max_requests:int=1
                   , timeout:int = 0
                   , timeinterval:int = 0
                   , api_key:Union[str, None]=None
                   , model:str = None
                   , update:bool = True
                   , **options)->Resp:
        """Get the API response

        Args:
            max_requests (int, optional): maximum number of requests to make. Defaults to 1.
            timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).   
            timeinterval (int, optional): time interval between two API calls. Defaults to 0.
            model (str, optional): model to use. Defaults to "gpt-3.5-turbo".
            update (bool, optional): whether to update the chat log. Defaults to True.
            **options : options inherited from the `openai.ChatCompletion.create` function.

        Returns:
            Resp: API response
        """
        if api_key is None:
            api_key = self.api_key
        assert api_key is not None, "API key is not set!"
        if model is None:
            model = self.model

        # initialize prompt message
        msg = self.chat_log
        # default options
        if not len(options):options = {}
        # make request
        resp = None
        numoftries = 0
        while max_requests:
            try:
                # Make the API call
                response = chat_completion(
                    api_key=api_key, messages=msg, model=model,
                    chat_url=self.chat_url, timeout=timeout, **options)
                time.sleep(random.random() * timeinterval)
                resp = Resp(response)
                assert resp.is_valid(), "Invalid response with message: " + resp.error_message
                break
            except Exception as e:
                max_requests -= 1
                numoftries += 1
                print(f"Try again ({numoftries}):{e}\n")
        else:
            raise Exception("Request failed! Try using `debug_log()` to find out the problem " +
                            "or increase the `max_requests`.")
        if update: # update the chat log
            self.assistant(resp.content)
        return resp
    
    def get_valid_models(self, gpt_only:bool=True)->List[str]:
        """Get the valid models

        Args:
            gpt_only (bool, optional): whether to only show the GPT models. Defaults to True.

        Returns:
            List[str]: valid models
        """
        return valid_models(self.api_key, gpt_only=gpt_only)

    def add(self, role:str, msg:str):
        """Add a message to the chat log"""
        assert role in ['user', 'assistant', 'system'], "role should be 'user', 'assistant' or 'system'"
        self._chat_log.append({"role": role, "content": msg})
        return self

    def user(self, msg:str):
        """User message"""
        return self.add('user', msg)
    
    def assistant(self, msg:str):
        """Assistant message"""
        return self.add('assistant', msg)
    
    def system(self, msg:str):
        """System message"""
        return self.add('system', msg)
    
    def clear(self):
        """Clear the chat log"""
        self._chat_log = []
    
    def copy(self):
        """Copy the chat log"""
        return Chat(self._chat_log)
    
    def last(self):
        """Get the last message"""
        return self._chat_log[-1]['content']

    def save(self, path:str, mode:str='a'):
        """
        Save the chat log to a file. Each line is a json string.

        Args:
            path (str): path to the file
            mode (str, optional): mode to open the file. Defaults to 'a'.
        """
        assert mode in ['a', 'w'], "saving mode should be 'a' or 'w'"
        data = self.chat_log
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        return
    
    def savewithid(self, path:str, chatid:int, mode:str='a'):
        """Save the chat log with chat id. Each line is a json string.

        Args:
            path (str): path to the file
            chatid (int): chat id
            mode (str, optional): mode to open the file. Defaults to 'a'.
        """
        assert mode in ['a', 'w'], "saving mode should be 'a' or 'w'"
        data = {"chatid": chatid, "chatlog": self.chat_log}
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        return

    def print_log(self, sep: Union[str, None]=None):
        """Print the chat log"""
        if sep is None:
            sep = '\n' + '-'*15 + '\n'
        for d in self._chat_log:
            print(sep, d['role'], sep, d['content'])
    
    def pop(self, ind:int=-1):
        """Pop the last message"""
        return self._chat_log.pop(ind)

    def __len__(self):
        """Length of the chat log"""
        return len(self._chat_log)
    
    def __repr__(self) -> str:
        return f"<Chat with {len(self)} messages>"
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __eq__(self, chat: object) -> bool:
        if isinstance(chat, Chat):
            return self._chat_log == chat._chat_log
        return False

    def __getitem__(self, index):
        """Get the message at index"""
        return self._chat_log[index]