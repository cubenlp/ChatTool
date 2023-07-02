# The object that stores the chat log

from typing import List, Dict, Union, Callable
import openai_api_call
from .response import Resp
from .request import chat_completion, usage_status, valid_models
import signal, time, random, datetime, json, warnings, docstring_parser

# timeout handler
def handler(signum, frame):
    raise Exception("API call timed out!")

# TODO: Generate a function description(Json Schema)
def func2desc(func:Callable) -> str:
    pass

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
        self._function_call = None
        self._functions = None
        self._available_functions = None
    
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

    @property
    def function_call(self):
        """Function call
        
        Control the behavior of the model. Can be "auto", "none" or a dict with only one key "name"
        
        Explanation:
            "auto": the model will automatically call the function if it thinks it is necessary
            "none": the model will never call the function
            {"name": "get_current_weather"}: the model will be forced to call the function "get_current_weather"
        """
        return self._function_call
    
    @function_call.setter
    def function_call(self, para:Union[None, str, Dict]):
        """Set value of function call

        Args:
            para (Union[None, str, Dict]): function call. Can be "auto", "none" or a dict with only one key "name"
        
        Examples:
            >>> chat = Chat()
            >>> chat.function_call = None
            >>> chat.function_call = "auto"
            >>> chat.function_call = "none"
            >>> chat.function_call = {"name": "get_current_weather"}
        """
        if para is not None:
            if isinstance(para, str):
                assert para in ["auto", "none"], "Function call should be either 'auto' or 'none'!"
            elif isinstance(para, dict):
                assert 'name' in para.keys() and len(para) == 1, "Function call should be a dict with only one key 'name'!"
            else:
                raise ValueError("Function call should be either 'auto', 'none' or a dict!")
        self._function_call = para
    
    @property
    def functions(self):
        """function list for the function calling feature"""
        return self._functions
    
    @functions.setter
    def functions(self, para:Union[None, List[Dict]]):
        """Set function list

        Args:
            para (Union[None, List[Dict]]): function list. Defaults to None.
        
        Examples:
            >>> chat = Chat()
            >>> chat.functions = None
            >>> chat.functions = [{
                "name": "get_current_weather",
                "description": "Get the current weather",
                "arguments": {
                    "location": {
                        "type": "string",
                        "description": "The location to get the weather for"
                    },
                    "time": {
                        "type": "string",
                        "description": "The time to get the weather for"
                    }
                }
            }]
        """
        if para is not None:
            assert isinstance(para, list), "Functions should be a list!"
            assert len(para), "Functions should not be empty!"
        self._functions = para

    @property
    def available_functions(self):
        """Available functions"""
        return self._available_functions
    
    @available_functions.setter
    def available_functions(self, funcs:Union[list, dict, None]):
        """Set available functions

        Args:
            funcs (Union[list, dict, None]): available functions. Defaults to None. 
                If it is a list, the function name will be used as the key.
        """
        assert funcs is None or isinstance(funcs, (list, dict)), "Available functions should be a list or a dict!"

        if funcs is None:
            self._available_functions = None
        elif not len(funcs): # empty list
            warnings.warn("No available functions!")
            self._available_functions = {}
        elif isinstance(funcs, list):
            # use function name as key
            self._available_functions = {func.__name__: func for func in funcs}
        else:
            self._available_functions = funcs
    
    def eval_func(self, call:dict, update:bool=True):
        name = call['name']
        func = self.available_functions.get(name)
        assert func is not None, f"Function {name} is not available!"
        args = json.loads(call['arguments'])
        result = func(**args)
        if update:
            self.function(name, result)
        return result
    
    def getresponse( self
                   , max_requests:int=1
                   , strip:bool=True
                   , update:bool = True
                   , timeout:int = 0
                   , timeinterval:int = 0
                   , api_key:Union[str, None]=None
                   , function_call:Union[None, str, Dict]=None
                   , evalfunc:bool=False
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
        # Two optional keys: "api_key" and "function_call"
        if api_key is None:
            api_key = self.api_key
        assert api_key is not None, "API key is not set!"
        if function_call is None:
            function_call = self.function_call
        # functions(Json schemas)
        functions = self.functions
        if function_call is not None:
            assert functions is not None, "`function_call` is only allowed when `functions` are specified."
        # available functions(dict)
        available_functions = self.available_functions

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
                    api_key=api_key, messages=msg, model=model, chat_url=self.chat_url,
                    function_call=self.function_call, functions=self.functions, **options)
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
            # The following is equivalent to `self.chat_log.append(resp.message))`
            if not resp.is_function_call():
                self.assistant(resp.content)
            else: # function call
                self.assistant(resp.content, call=resp.function_call)
                if evalfunc:
                    assert available_functions is not None, "Please specify the available functions!"
                    self.eval_func(resp.function_call, update=True)
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
        print(f"Amount: {storage:.4f}$")
        if thismonth:
            print(f"Usage(this month): {usage:.4f}$")
            print(f"Remaining(this month): {rem:.4f}$")
        if len(recent_usage) > 0:
            usage = sum(recent_usage.values())
            print(f"Usage(the last {len(recent_usage)} days): {usage:.4f}$")
        for date, cost in recent_usage.items():
            print(f"{date}: {cost:.4f}$")

    def get_valid_models(self, gpt_only:bool=True)->List[str]:
        """Get the valid models

        Args:
            gpt_only (bool, optional): whether to only show the GPT models. Defaults to True.

        Returns:
            List[str]: valid models
        """
        return valid_models(self.api_key, gpt_only=gpt_only)

    def add( self
           , role:str
           , content:Union[None, str]=None
           , function_call:Union[None, str]=None
           , name:Union[None, str]=None):
        """Add a role message to the chat log
        
        This is the wrapper of the `message` part of the `openai.ChatCompletion.create` function.

        Args:
            role (str): role of the message, should be 'user', 'assistant', 'system' or 'function'.
            content (object): content of the message, it can be None, str, or object of function response.
            function_call (Union[None, dict], optional): function call, arguments of the function. Defaults to None.
            name (Union[None, str], optional): name of the function. Defaults to None.
        """
        assert role in ['user', 'assistant', 'system', 'function'], "role should be 'user', 'assistant', 'system' or 'function'!"
        # same as before
        if role == 'system' or role == 'user' \
            or (role == 'assistant' and function_call is None):
            assert content is not None, "Invalid format: The content should not be None!"
            self._chat_log.append({"role": role, "content": content})
        # assistant with function call
        elif role == 'assistant':
            if content is not None:
                warnings.warn("The content will be ignored when `function_call` is specified!")
            self._chat_log.append({"role": role, "content": content, "function_call": function_call})
        # function call
        elif role == 'function':
            assert name is not None, "Invalid format: The name of fucntion should be specified!"
            self._chat_log.append({"role": role, "name": name, "content": content})
        return self

    def user(self, content:str):
        """User message"""
        return self.add('user', content)
    
    def assistant(self, content:Union[None, str], call:Union[None, str]=None):
        """Assistant message"""
        return self.add('assistant', content, function_call=call)
    
    def system(self, content:str):
        """System message"""
        return self.add('system', content)

    def function(self, funcname:str, funcresp:str):
        """Function call"""
        return self.add('function', name=funcname, content=funcresp)
    
    def clear(self):
        """Clear the chat log"""
        self._chat_log = []
    
    def copy(self):
        """Copy the chat log"""
        return Chat(self._chat_log)

    def save(self, path:str, mode:str='a', end:str='\n', chatid:int=-1):
        """
        Save the chat log to a file

        Args:
            path (str): path to the file
            mode (str, optional): mode to open the file. Defaults to 'a'.
            end (str, optional): end of each line. Defaults to '\n'.
            chatid (int, optional): chat id. Defaults to -1.
        """
        assert mode in ['a', 'w'], "mode should be 'a' or 'w'"
        data = self.chat_log
        if chatid >= 0:
            data = {'chatid': chatid, 'chatlog': data}
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + end)
        return
        
    def print_log(self, sep: Union[str, None]=None):
        """Print the chat log"""
        if sep is None:
            sep = '\n' + '-'*15 + '\n'
        for d in self._chat_log:
            print(sep, d['role'], sep)
            print(d['content'])
    
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
        return self._chat_log[index]['content']
