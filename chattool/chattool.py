# The object that stores the chat log

from typing import List, Dict, Union
import chattool
from .response import Resp
from .tokencalc import num_tokens_from_messages
from .request import chat_completion, valid_models
import time, random, json
import aiohttp
from .functioncall import generate_json_schema, delete_dialogue_assist

class Chat():
    def __init__( self
                , msg:Union[List[Dict], None, str]=None
                , api_key:Union[None, str]=None
                , chat_url:Union[None, str]=None
                , base_url:Union[None, str]=None
                , model:Union[None, str]=None
                , functions:Union[None, List[Dict]]=None
                , function_call:Union[None, str]=None
                , name2func:Union[None, Dict]=None):
        """Initialize the chat log

        Args:
            msg (Union[List[Dict], None, str], optional): chat log. Defaults to None.
            api_key (Union[None, str], optional): API key. Defaults to None.
            chat_url (Union[None, str], optional): base url. Defaults to None. Example: "https://api.openai.com/v1/chat/completions"
            base_url (Union[None, str], optional): base url. Defaults to None. Example: "https://api.openai.com"
            model (Union[None, str], optional): model to use. Defaults to None.
            functions (Union[None, List[Dict]], optional): functions to use, each function is a JSON Schema. Defaults to None.
            function_call (str, optional): method to call the function. Defaults to None. Choices: ['auto', '$NameOfTheFunction', 'none']
            name2func (Union[None, Dict], optional): name to function mapping. Defaults to None.
        
        Raises:
            ValueError: msg should be a list of dict, a string or None
        """
        if msg is None:
            self._chat_log = []
        elif isinstance(msg, str):
            if chattool.default_prompt is None:
                self._chat_log = [{"role": "user", "content": msg}]
            else:
                self._chat_log = chattool.default_prompt(msg)
        elif isinstance(msg, list):
            self._chat_log = msg.copy() # avoid changing the original list
        else:
            raise ValueError("msg should be a list of dict, a string or None")
        self._api_key = api_key or chattool.api_key
        self._base_url = base_url or chattool.base_url
        self._chat_url = chat_url or self._base_url.rstrip('/') + '/v1/chat/completions'
        self._model = model or 'gpt-3.5-turbo'
        if functions is not None:
            assert isinstance(functions, list), "functions should be a list of dict"
        self._functions, self._function_call = functions, function_call
        self._name2func, self._resp = name2func, None
    
    # Part1: basic operation of the chat object
    def add(self, role:str, **kwargs):
        """Add a message to the chat log"""
        assert role in ['user', 'assistant', 'system', 'function'],\
            f"role should be one of ['user', 'assistant', 'system', 'function'], but got {role}"
        self._chat_log.append({'role':role, **kwargs})
        return self

    def user(self, content:str):
        """User message"""
        return self.add('user', content=content)
    
    def assistant(self, content:Union[None, str], function_call:Union[None, Dict]=None):
        """Assistant message"""
        if function_call is not None:
            assert isinstance(function_call, dict), "function_call should be a dict"
            return self.add('assistant', content=content, function_call=function_call)
        return self.add('assistant', content=content)
    
    def function(self, content, name:str, dump:bool=True):
        """Add a message to the chat log"""
        if dump: content = json.dumps(content)
        return self.add('function', content=content, name=name)
        
    def system(self, content:str):
        """System message"""
        return self.add('system', content=content)
    
    def clear(self):
        """Clear the chat log"""
        self._chat_log = []
    
    def copy(self):
        """Copy the chat log"""
        return Chat(self._chat_log)
    
    def deepcopy(self):
        """Deep copy the Chat object"""
        return Chat( self._chat_log
                   , api_key=self.api_key
                   , chat_url=self.chat_url
                   , model=self.model
                   , functions=self.functions
                   , function_call=self.function_call
                   , name2func=self.name2func
                   , base_url=self.base_url)

    def save(self, path:str, mode:str='a'):
        """
        Save the chat log to a file. Each line is a json string.

        Args:
            path (str): path to the file
            mode (str, optional): mode to open the file. Defaults to 'a'.
        """
        assert mode in ['a', 'w'], "saving mode should be 'a' or 'w'"
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(self.chat_log, ensure_ascii=False) + '\n')
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
    
    def savewithmsg(self, path:str, mode:str='a'):
        """Save the chat log with message.

        Args:
            path (str): path to the file
            mode (str, optional): mode to open the file. Defaults to 'a'.
        """
        assert mode in ['a', 'w'], "saving mode should be 'a' or 'w'"
        data = {"messages": self.chat_log}
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        return
    
    @staticmethod
    def display_role_content(dic:dict, sep:Union[str, None]=None):
        """Show the role and content of the message"""
        if sep is None: sep = '\n' + '-'*15 + '\n'
        role, content = dic['role'], dic['content']
        if role == 'user' or role == 'system' or (role == 'assistant' and 'function_call' not in dic):
            return f"{sep}{role}{sep}{dic['content']}"
        elif role == 'function':
            return f"{sep}{role}{sep}function:\n\t{dic['name']}\nresult:\n\t{content}"
        elif role == 'assistant':
            return f"{sep}{role}{sep}calling function:\n\t{dic['function_call']}\ncontent:\n\t{content}"
        else:
            raise Exception(f"Unknown role {role}")
    
    def print_log(self, sep: Union[str, None]=None):
        """Print the chat log"""
        for resp in self.chat_log:
            print(self.display_role_content(resp, sep=sep))
    
    # Part2: response and async response
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
        funcs = options.get('functions', self.functions)
        func_call = options.get('function_call', self.function_call)
        assert api_key is not None, "API key is not set!"
        msg, resp, numoftries = self.chat_log, None, 0
        if stream: # TODO: add the `usage` key to the response
            print("Warning: stream mode is not supported yet! Use `async_stream_responses()` instead.")
        # make requests
        while max_requests:
            try:
                # make API Call
                if funcs is not None: options['functions'] = funcs
                if func_call is not None: options['function_call'] = func_call
                response = chat_completion(
                    api_key=api_key, messages=msg, model=model,
                    chat_url=self.chat_url, timeout=timeout, **options)
                resp = Resp(response)
                assert resp.is_valid(), resp.error_message
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
            self._chat_log.append(resp.message)
            self._resp = resp
        return resp
    
    async def async_stream_responses(self, timeout=0):
        """Post request asynchronously and stream the responses

        Args:
            timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
        
        Returns:
            str: response text
        """
        # TODO: Support other options
        data = json.dumps({
            "model" : self.model, "messages" : self.chat_log, "stream":True})
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.api_key}
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
    
    # Part3: function call
    def iswaiting(self):
        """Whether the response is waiting"""
        if len(self) == 0: return False
        return self[-1]['role'] == 'assistant' and 'function_call' in self[-1]

    @staticmethod
    def get_name_and_params(dic:dict):
        """Get the name and parameters of the function call"""
        if 'role' in dic and 'function_call' in dic:
            dic = dic['function_call']
        name, params = dic['name'], json.loads(dic['arguments'])
        return name, params
    
    def simplify(self):
        """Simplify the chat log"""
        delete_dialogue_assist(self.chat_log)
        return self
    
    def setfuncs(self, funcs:List):
        """Initialize function for function call"""
        self.functions = [generate_json_schema(func) for func in funcs]
        self.function_call = 'auto'
        self.name2func = {func.__name__:func for func in funcs}
        return True

    def callfunction(self):
        """Calling function"""
        if not self.iswaiting():
            return False, "Not waiting for function call."
        name = self[-1]['function_call']['name']
        if name not in self.name2func:
            return False, f"Function {name} not found."
        try:
            args = json.loads(self[-1]['function_call']['arguments'])
        except Exception as e:
            return False, f"Cannot parse the arguments, error: {e}"
        try:
            result = self.name2func[name](**args)
        except Exception as e:
            return False, f"Function {name} failed with error: {e}"
        # succeed finally!
        self.function(result, name)
        return True, "Function called successfully."
    
    def autoresponse( self
                    , display:bool=False
                    , maxturns:int=3
                    , capturerr:bool=True
                    , **options):
        """Get the response automatically
        
        Args:
            display (bool, optional): whether to display the response. Defaults to False.
            maxturns (int, optional): maximum number of turns. Defaults to 3.
            capturerr (bool, optional):  if True, use the error message as the response. Defaults to True.
            options (dict, optional): other options like `temperature`, `top_p`, etc.

        Returns:
            bool: whether the response is finished
        """
        options['functions'], options['function_call'] = self.functions, self.function_call
        show = lambda msg: print(self.display_role_content(msg))
        resp = self.getresponse(**options)
        if display: show(resp.message)
        while self.iswaiting() and maxturns != 0:
            # call api and update the result
            status, msg = self.callfunction()
            if not status: # update the error msg
                if not capturerr: return False
                self.function(msg, 'error')
            if display: show(self[-1])
            resp = self.getresponse(**options)
            if display: show(resp.message)
            maxturns -= 1
        return True
    
    # Part4: other functions
    def get_valid_models(self, gpt_only:bool=True)->List[str]:
        """Get the valid models

        Args:
            gpt_only (bool, optional): whether to only show the GPT models. Defaults to True.

        Returns:
            List[str]: valid models
        """
        return valid_models(self.api_key, self.base_url, gpt_only=gpt_only)

    def prompt_token(self, model:str="gpt-3.5-turbo-0613"):
        """Get the prompt token for the model

        Args:
            model (str): model to use

        Returns:
            str: prompt token
        """
        return num_tokens_from_messages(self.chat_log, model=model)
    
    # Part5: properties and setters
    @property
    def last_message(self):
        """Get the last message"""
        return self._chat_log[-1]['content']

    @property
    def last_response(self):
        """Get the latest response"""
        return self._resp
    
    @property
    def last_cost(self):
        """Get the latest cost"""
        return self._resp.cost() if self._resp is not None else None

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
    
    @property
    def base_url(self):
        """Get base url"""
        return self._base_url
    
    @property
    def functions(self):
        """Get functions"""
        return self._functions
    
    @property
    def function_call(self):
        """Get function call"""
        return self._function_call

    @property
    def name2func(self):
        """Get name to function mapping"""
        return self._name2func
    
    @api_key.setter
    def api_key(self, api_key:str):
        """Set API key"""
        self._api_key = api_key
    
    @chat_url.setter
    def chat_url(self, chat_url:str):
        """Set base url"""
        self._chat_url = chat_url

    @base_url.setter
    def base_url(self, base_url:str):
        """Set base url"""
        self._base_url = base_url

    @functions.setter
    def functions(self, functions:List[Dict]):
        """Set functions"""
        assert isinstance(functions, list), "functions should be a list of dict"
        self._functions = functions
    
    @function_call.setter
    def function_call(self, function_call:str):
        """Set function call"""
        if function_call in ['auto', None, 'none']:
            self._function_call = function_call
        elif isinstance(function_call, str):
            self.function_call = {'name':function_call}
        elif isinstance(function_call, dict):
            assert 'name' in function_call
            self._function_call = function_call
    
    @name2func.setter
    def name2func(self, name2func:Dict):
        """Set name to function mapping"""
        assert isinstance(name2func, dict), "name2func should be a dict"
        self._name2func = name2func
    
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
    
    def __eq__(self, chat: object) -> bool:
        if isinstance(chat, Chat):
            return self._chat_log == chat._chat_log
        return False

    def __getitem__(self, index):
        """Get the message at index"""
        return self._chat_log[index]
