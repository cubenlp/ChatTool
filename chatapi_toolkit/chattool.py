# The object that stores the chat log

from typing import List, Dict, Union
import chatapi_toolkit
from .response import Resp
from .tokencalc import num_tokens_from_messages, token2cost
from .request import chat_completion, valid_models
import time, random, json
import aiohttp

class Chat():
    def __init__( self
                , msg:Union[List[Dict], None, str]=None
                , api_key:Union[None, str]=None
                , chat_url:Union[None, str]=None
                , model:Union[None, str]=None):
        """Initialize the chat log

        Args:
            msg (Union[List[Dict], None, str], optional): chat log. Defaults to None.
            api_key (Union[None, str], optional): API key. Defaults to None.
            chat_url (Union[None, str], optional): base url. Defaults to None. Example: "https://api.openai.com/v1/chat/completions"
            model (Union[None, str], optional): model to use. Defaults to None.
        
        Raises:
            ValueError: msg should be a list of dict, a string or None
        """
        if msg is None:
            self._chat_log = []
        elif isinstance(msg, str):
            if chatapi_toolkit.default_prompt is None:
                self._chat_log = [{"role": "user", "content": msg}]
            else:
                self._chat_log = chatapi_toolkit.default_prompt(msg)
        elif isinstance(msg, list):
            self._chat_log = msg.copy() # avoid changing the original list
        else:
            raise ValueError("msg should be a list of dict, a string or None")
        self._api_key = chatapi_toolkit.api_key if api_key is None else api_key
        self._chat_url = chat_url if chat_url is not None else\
              chatapi_toolkit.base_url.rstrip('/') + '/v1/chat/completions'
        self._model = 'gpt-3.5-turbo' if model is None else model
        self._resp = None
    
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
                   , update:bool = True
                   , stream:bool = False
                   , **options)->Resp:
        """Get the API response

        Args:
            max_requests (int, optional): maximum number of requests to make. Defaults to 1.
            timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
            timeinterval (int, optional): time interval between two API calls. Defaults to 0.
            update (bool, optional): whether to update the chat log. Defaults to True.
            options (dict, optional): other options like `temperature`, `top_p`, etc.

        Returns:
            Resp: API response
        """
        # initialize data
        api_key, model = self.api_key, self.model
        assert api_key is not None, "API key is not set!"
        if not len(options):options = {}
        msg, resp, numoftries = self.chat_log, None, 0
        if stream: # TODO: add the `usage` key to the response
            print("Warning: stream mode is not supported yet! Use `async_stream_responses()` instead.")
        # make requests
        while max_requests:
            try:
                # Make the API call
                response = chat_completion(
                    api_key=api_key, messages=msg, model=model,
                    chat_url=self.chat_url, timeout=timeout, **options)
                resp = Resp(response)
                assert resp.is_valid(), "Invalid response with message: " + resp.error_message
                break
            except Exception as e:
                max_requests -= 1
                numoftries += 1
                time.sleep(random.random() * timeinterval)
                print(f"Try again ({numoftries}):{e}\n")
        else:
            raise Exception("Request failed! Try using `debug_log()` to find out the problem " +
                            "or increase the `max_requests`.")
        if update: # update the chat log
            self.assistant(resp.content)
            self._resp = resp
        return resp
    
    async def async_stream_responses(self, timeout=0):
        """Post request asynchronously and stream the responses

        Args:
            timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
        
        Returns:
            str: response text
        """
        data = json.dumps({
            "model" : self.model, "messages" : self.chat_log, "stream":True})
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.api_key}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.chat_url, headers=headers, data=data, timeout=timeout) as response:
                    while True:
                        line = await response.content.readline()
                        if not line: break
                        strline = line.decode().lstrip('data:').strip()
                        if not strline: continue
                        line = json.loads(strline)
                        resp = Resp(line)
                        if resp.finish_reason == 'stop': break
                        yield resp
        except Exception as e:
            raise Exception(f"Request Failed:{e}")
    
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
        return Chat(self._chat_log, api_key=self.api_key, chat_url=self.chat_url, model=self.model)
    
    def last_message(self):
        """Get the last message"""
        return self._chat_log[-1]['content']

    def latest_response(self):
        """Get the latest response"""
        return self._resp
    
    def latest_cost(self):
        """Get the latest cost"""
        return self._resp.cost() if self._resp is not None else None

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
    