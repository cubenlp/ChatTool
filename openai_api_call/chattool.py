# The object that stores the chat log

from typing import List, Dict, Union
import openai_api_call
from .response import Resp
from .request import chat_completion, usage_status
import signal, time, random
import datetime
import json

# timeout handler
def handler(signum, frame):
    raise Exception("API call timed out!")

class Chat():
    def __init__( self
                , msg:Union[List[Dict], None, str]=None
                , api_key:Union[None, str]=None) -> None:
        """Chat object
        
        Args:
            msg (Union[List[Dict], None, str], optional): chat log. Defaults to None.
            api_key (Union[None, str], optional): API key. Defaults to None.

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
        if api_key is None:
            self._api_key = openai_api_call.api_key
    
    @property
    def api_key(self):
        """Get API key"""
        return self._api_key
    
    @api_key.setter
    def api_key(self, api_key:str):
        """Set API key"""
        self._api_key = api_key
    
    def getresponse( self
                   , max_requests:int=1
                   , strip:bool=True
                   , update:bool = True
                   , timeout:int = 0
                   , timeinterval:int = 0
                   , api_key:Union[str, None]=None
                   , model:str = "gpt-3.5-turbo"
                   , **options)->Resp:
        """Get the API response

        Args:
            max_requests (int, optional): maximum number of requests to make. Defaults to 1.
            strip (bool, optional): whether to strip the prompt message. Defaults to True.
            update (bool, optional): whether to update the chat log. Defaults to True.
            timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).   
            timeinterval (int, optional): time interval between two API calls. Defaults to 0.
            model (str, optional): model to use. Defaults to "gpt-3.5-turbo".
            **options : options inherited from the `openai.ChatCompletion.create` function.

        Returns:
            Resp: API response
        """
        if api_key is None:
            api_key = self.api_key
        assert api_key is not None, "API key is not set!"

        # initialize prompt message
        msg = self.chat_log
        # default options
        if not len(options):options = {}
        # make request
        resp = None
        numoftries = 0
        # Set the timeout handler
        signal.signal(signal.SIGALRM, handler)
        while max_requests:
            try:
                # Set the alarm to trigger after `timeout` seconds
                signal.alarm(timeout)
                # Make the API call
                response = chat_completion(
                    api_key=api_key, messages=msg, model=model, **options)
                time.sleep(random.random() * timeinterval)
                resp = Resp(response, strip=strip)
                assert resp.is_valid(), "Invalid response with message: " + resp.error_message
                break
            except Exception as e:
                max_requests -= 1
                numoftries += 1
                print(f"API call failed with message: {e}\nTry again ({numoftries})")
            finally:
                # Disable the alarm after execution
                signal.alarm(0)
        else:
            raise Exception("Failed to get the response!\nYou can try to update the API key"
                            + ", increase `max_requests` or set proxy.")
        if update: # update the chat log
            self.assistant(resp.content)
        return resp

    def get_usage_status(self, recent:int=10, duration:int=99):
        """Get the usage status
        
        Args:
            recent (int, optional): number of the usage of recent days. Defaults to 10.
            duration (int, optional): duration of the usage. Defaults to 99.
        
        Returns:
            str: usage status
        """
        storage, usage, dailyusage = usage_status(self.api_key, duration=duration)
        status = [storage, usage, storage-usage, {}]
        if recent <= 0 or len(dailyusage) == 0: # no need to print the usage of recent days
            return status
        recent = min(recent, len(dailyusage)) # number of recent days
        dailyusage = dailyusage[-recent:]
        for day in dailyusage:
            date = datetime.datetime.fromtimestamp(day.get("timestamp")).strftime("%Y-%m-%d")
            line_items = day.get("line_items")
            cost = sum([item.get("cost") for item in line_items]) / 100
            status[-1].update({date: cost})
        return status
    
    def show_usage_status(self, thismonth:bool=True, recent:int=10, duration:int=99):
        """Show the usage status
        
        Args:
            thismonth (bool): 
            recent (int, optional): number of the usage of recent days. Defaults to 10.
            duration (int, optional): duration of the usage. Defaults to 99.
        """
        if thismonth:
            duration = datetime.datetime.now().day - 1
        storage, usage, rem, recent_usage = self.get_usage_status(recent=recent, duration=duration)
        print(f"Total account: {storage:.4f}$")
        print(f"Total usage(the last {len(recent_usage)} days): {usage:.4f}$")
        if thismonth:
            print(f"Total remaining(this month): {rem:.4f}$")
        for date, cost in recent_usage.items():
            print(f"{date}: {cost:.4f}$")

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

    def save(self, path:str, mode:str='a', end:str='\n'):
        """
        Save the chat log to a file

        Args:
            path (str): path to the file
            mode (str, optional): mode to open the file. Defaults to 'a'.
            end (str, optional): end of each line. Defaults to '\n'.
        """
        assert mode in ['a', 'w'], "mode should be 'a' or 'w'"
        data = self.chat_log
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data) + end)
        return True
        
    def print_log(self, sep: Union[str, None]=None):
        """Print the chat log"""
        if sep is None:
            sep = '\n' + '-'*15 + '\n'
        for d in self._chat_log:
            print(sep, d['role'], sep, d['content'])
    
    @property
    def chat_log(self):
        """Chat history"""
        return self._chat_log
    
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

    def __getitem__(self, index):
        """Get the message at index"""
        return self._chat_log[index]['content']