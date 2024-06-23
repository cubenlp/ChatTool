# The object that stores the chat log

from typing import List, Dict, Union
import chattool
from .response import Resp
from .request import chat_completion, valid_models, curl_cmd_of_chat_completion
import time, random, json, warnings
import aiohttp
import os
from .functioncall import generate_json_schema, delete_dialogue_assist
from pprint import pformat
from loguru import logger

class Chat():
    def __init__( self
                , msg:Union[List[Dict], None, str]=None
                , api_key:Union[None, str]=None
                , api_base:Union[None, str]=None
                , base_url:Union[None, str]=None
                , chat_url:Union[None, str]=None
                , model:Union[None, str]=None
                , tools:Union[None, List[Dict]]=None
                , tool_choice:Union[None, str]=None
                , tool_type:str='tool_choice'
                , functions:Union[None, List[Dict]]=None
                , function_call:Union[None, str]=None
                , name2func:Union[None, Dict]=None):
        """Initialize the chat log

        Args:
            msg (Union[List[Dict], None, str], optional): chat log. Defaults to None.
            api_key (Union[None, str], optional): API key. Defaults to None.
            api_base (Union[None, str], optional): base url with suffix "/v1". Defaults to None. Example: "https://api.openai.com/v1"
            base_url (Union[None, str], optional): base url without suffix "/v1". Defaults to None. Example: "https://api.openai.com"
            chat_url (Union[None, str], optional): chat completion url. Defaults to None. Example: "https://api.openai.com/v1/chat/completions"
            model (Union[None, str], optional): model to use. Defaults to None.
            tools (Union[None, List[Dict]], optional): tools to use, each tool is a JSON Schema. Defaults to None.
            tool_choice (Union[None, str], optional): method to choose the tool. Defaults to None. Choices: ['auto', '$NameOfTheTool', 'none']
            name2func (Union[None, Dict], optional): name to function mapping. Defaults to None.
            functions (Union[None, List[Dict]], optional): Decrpcated. functions to use, each function is a JSON Schema. Defaults to None.
            function_call (str, optional): Decrpcated. method to call the function. Defaults to None. Choices: ['auto', '$NameOfTheFunction', 'none']
            
        
        Raises:
            ValueError: msg should be a list of dict, a string or None
        """
        # initial message
        if msg is None:
            self._chat_log = []
        elif isinstance(msg, str):
            self._chat_log = chattool.default_prompt(msg)
        elif isinstance(msg, list):
            assert all(isinstance(m, dict) for m in msg), "msg should be a list of dict"
            self._chat_log = msg.copy() # avoid changing the original list
        else:
            raise ValueError("msg should be a list of dict, a string or None")
        self.api_key = api_key or chattool.api_key or ''
        self.model = model or chattool.model or ''
        # chat_url > api_base > base_url > chattool.api_base > chattool.base_url
        self.api_base = api_base or chattool.api_base
        self.base_url = base_url or chattool.base_url
        if chat_url:
            self.chat_url = chat_url
        elif api_base:
            self.chat_url = os.path.join(self.api_base, "chat/completions")
        elif base_url:
            self.chat_url = os.path.join(self.base_url, "v1/chat/completions")
        elif chattool.api_base:
            self.chat_url = os.path.join(chattool.api_base, "chat/completions")
        elif chattool.base_url:
            self.chat_url = os.path.join(chattool.base_url, "v1/chat/completions")
        else:
            self.chat_url = "https://api.openai.com/v1/chat/completions"
        # functions and tools
        if functions is not None:
            assert isinstance(functions, list), "functions should be a list of dict"
        if tools is not None:
            assert isinstance(tools, list), "tools should be a list of dict"
        self.tool_type = tool_type
        self.functions, self.tools = functions or [], tools or []
        self._function_call, self._tool_choice = function_call, tool_choice
        self._name2func, self._resp = name2func, None
    
    # Part1: basic operation of the chat object
    def add(self, role:str, **kwargs):
        """Add a message to the chat log"""
        assert role in ['user', 'assistant', 'system', 'tool', 'function'],\
            f"role should be one of ['user', 'assistant', 'system', 'tool'], but got {role}"
        self._chat_log.append({'role':role, **kwargs})
        return self

    def user(self, content: Union[List, str]):
        """User message"""
        return self.add('user', content=content)
    
    def assistant(self, content:Union[None, str]):
        """Assistant message"""
        return self.add('assistant', content=content)
    
    def function(self, content, name:str, dump:bool=True):
        """Add a message to the chat log"""
        if dump: content = json.dumps(content)
        return self.add('function', content=content, name=name)
    
    def tool(self, content, name:str, tool_call_id:str, dump:bool=True):
        """Add a message to the chat log"""
        if dump: content = json.dumps(content)
        return self.add('tool', content=content, name=name, tool_call_id=tool_call_id)
        
    def system(self, content:str):
        """System message"""
        return self.add('system', content=content)
    
    def clear(self):
        """Clear the chat log"""
        self._chat_log = []
    
    def copy(self):
        """Copy the chat log"""
        return Chat(self.chat_log)
    
    def deepcopy(self):
        """Deep copy the Chat object"""
        return Chat( self.chat_log
                   , api_key=self.api_key
                   , chat_url=self.chat_url
                   , model=self.model
                   , functions=self.functions
                   , function_call=self.function_call
                   , tools=self.tools
                   , tool_choice=self.tool_choice
                   , name2func=self.name2func
                   , api_base=self.api_base
                   , base_url=self.base_url)

    def save(self, path:str, mode:str='a', index:int=0):
        """
        Save the chat log to a file. Each line is a json string.

        Args:
            path (str): path to the file
            mode (str, optional): mode to open the file. Defaults to 'a'.
        """
        assert mode in ['a', 'w'], "saving mode should be 'a' or 'w'"
        # make path if not exists
        pathname = os.path.dirname(path).strip()
        if pathname != '':
            os.makedirs(pathname, exist_ok=True)
        data = {"index": index, "chat_log": self.chat_log}
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        return
    
    def savewithmsg(self, path:str, mode:str='a'):
        """Save the chat log with message.
        This is for fine-tuning the model.

        Args:
            path (str): path to the file
            mode (str, optional): mode to open the file. Defaults to 'a'.
        """
        assert mode in ['a', 'w'], "saving mode should be 'a' or 'w'"
        # make path if not exists
        pathname = os.path.dirname(path).strip()
        if pathname != '':
            os.makedirs(pathname, exist_ok=True)
        data = {"messages": self.chat_log}
        with open(path, mode, encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        return
    
    @staticmethod
    def load(path:str):
        """Load the chat log from a file. Each line is a json string.

        Args:
            path (str): path to the file
        """
        with open(path, 'r', encoding='utf-8') as f:
            chat_log = json.loads(f.read())
        return Chat(chat_log['chat_log'])
    
    @staticmethod
    def display_role_content(dic:dict, sep:Union[str, None]=None):
        """Show the role and content of the message"""
        if sep is None: sep = '\n' + '-'*15 + '\n'
        role, content, name, tools = dic['role'], dic.get('content'), dic.get('name'), dic.get('tool_calls')
        if role == 'user' or role == 'system':
            return f"{sep}{role}{sep}{content}"
        elif role == 'tool':
            return f"{sep}{role}{sep}tool:\n\t{name}\nresult:\n\t{content}"
        elif role == 'function':
            return f"{sep}{role}{sep}function:\n\t{name}\nresult:\n\t{content}"
        elif role == 'assistant':
            if 'tool_calls' in dic:
                return f"{sep}{role}{sep}calling tool:\n{pformat(tools)}"
            if 'function_call' in dic:
                return f"{sep}{role}{sep}calling function:\n{pformat(dic['function_call'])}"
            return f"{sep}{role}{sep}{content}"
        else:
            raise Exception(f"Unknown role {role}")
    
    def print_log(self, sep: Union[str, None]=None):
        """Print the chat log"""
        for resp in self.chat_log:
            print(self.display_role_content(resp, sep=sep))
    
    # Part2: response and async response
    def getresponse( self
                   , max_tries:int = 1
                   , timeinterval:Union[float, int] = 0
                   , update:bool = True
                   , max_requests:int=-1
                   , **options)->Resp:
        """Get the API response

        Args:
            max_tries (int, optional): maximum number of requests to make. Defaults to 1.
            model (str, optional): model to use. Defaults to None.
            timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
            timeinterval (int, optional): time interval between two API calls. Defaults to 0.
            update (bool, optional): whether to update the chat log. Defaults to True.
            options (dict, optional): other options like `temperature`, `top_p`, etc.
            tool_type (str, optional): type of the tool. Defaults to None. Choices: ['tool_choice', 'function_call']
            tools (Union[None, List[Dict]], optional): tools to use, each tool is a JSON Schema. Defaults to None.
            tool_choice (Union[None, str], optional): method to choose the tool. Defaults to None. Choices: ['auto', '$NameOfTheTool', 'none']
            functions (Union[None, List[Dict]], optional): Decrpcated. functions to use, each function is a JSON Schema. Defaults to None.
            function_call (str, optional): Decrpcated. method to call the function. Defaults to None. Choices: ['auto', '$NameOfTheFunction', 'none']
            max_requests (int, optional): (deprecated) maximum number of requests to make. Defaults to -1(no limit)

        Returns:
            Resp: API response
        """
        # other options
        max_tries = max(max_tries, max_requests)
        if options.get('stream'):
            options['stream'] = False
            warnings.warn("Use `async_stream_responses()` instead.")
        options = self._init_options(**options)
        # make requests
        api_key, chat_log, chat_url = self.api_key, self.chat_log, self.chat_url
        resp = self._getresponse(api_key, chat_url, chat_log, max_tries, timeinterval, **options)
        if update: # update the chat log
            self._chat_log.append(resp.message)
            self._resp = resp
        return resp
    
    async def async_stream_responses( self
                                    , timeout:int=0
                                    , textonly:bool=False
                                    , **options):
        """Post request asynchronously and stream the responses

        Args:
            timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
            textonly (bool, optional): whether to only return the text. Defaults to False.
            options (dict, optional): other options like `temperature`, `top_p`, etc.
        
        Returns:
            str: response text
        """
        async for resp in _async_stream_responses(
            self.api_key, self.chat_url, self.chat_log, self.model, timeout=timeout, **options):
            yield resp.delta_content if textonly else resp
    
    # Part3: tool call
    def iswaiting(self):
        """Whether the response is waiting"""
        if len(self) == 0: return False
        return self[-1]['role'] == 'assistant' and ('tool_calls' in self[-1] or 'function_call' in self[-1])

    @staticmethod
    def get_name_and_params(dic:dict):
        """Get the name and parameters of the tool call"""
        if 'role' in dic and 'tool_calls' in dic:
            dic = dic['tool_calls']
        elif 'role' in dic and 'function_call' in dic:
            dic = dic['function_call'] 
        name, params = dic['name'], json.loads(dic['arguments'])
        return name, params
    
    def simplify(self):
        """Simplify the chat log"""
        delete_dialogue_assist(self.chat_log)
        return self
    
    def setfuncs(self, funcs:List):
        """Initialize function for tool calls"""
        self.functions = [generate_json_schema(func) for func in funcs]
        self.function_call = 'auto'
        self.name2func = {func.__name__:func for func in funcs}
        return True
    
    def settools(self, tools:List):
        """Initialize tools for tool calls"""
        self.functions =[generate_json_schema(func) for func in tools]
        self.tool_choice = 'auto' # the only difference from setfuncs
        self.name2func = {tool.__name__:tool for tool in tools}
        return True
    
    def calltools(self, display:bool=False):
        """Call all the tools"""
        if not self.iswaiting():
            return False, "Not waiting for tool call."
        tool_calls = self[-1]['tool_calls']
        allright = True
        for tool in tool_calls:
            result, name, tool_call_id, status = self.calltool(tool)
            self.tool(result, name, tool_call_id)
            if display: print(self.display_role_content(self[-1]))
            allright = allright and status
        return allright
        
    def calltool(self, tool):
        """Call the tool"""
        tool_call_id = tool.get('id')
        tool_name, tool_para = tool['function']['name'], tool['function']['arguments']
        if tool_name not in self.name2func:
            return f"Tool {tool_name} not found.", tool_name, tool_call_id, False
        try:
            tool_args = json.loads(tool_para)
        except Exception as e:
            return f"Argument parsing failed with error: {e}", tool_name, tool_call_id, False
        try:
            result = self.name2func[tool_name](**tool_args)
        except Exception as e:
            return f"Tool {tool_name} failed with error: {e}", tool_name, tool_call_id, False
        # succeed finally!
        return result, tool_name, tool_call_id, True

    def callfunction(self):
        """Calling function"""
        if not self.iswaiting():
            return "Not waiting for function call.", name
        name = self[-1]['function_call']['name']
        if name not in self.name2func:
            return f"Function {name} not found.", name, False
        try:
            args = json.loads(self[-1]['function_call']['arguments'])
        except Exception as e:
            return f"Cannot parse the arguments, error: {e}", name, False
        try:
            result = self.name2func[name](**args)
        except Exception as e:
            return f"Function {name} failed with error: {e}", name, False
        # succeed finally!
        return result, name, True
    
    def autoresponse( self
                    , display:bool=False
                    , maxturns:int=3
                    , tool_type:str='tool_choice'
                    , **options):
        """Get the response automatically
        
        Args:
            display (bool, optional): whether to display the response. Defaults to False.
            maxturns (int, optional): maximum number of turns. Defaults to 3.
            options (dict, optional): other options like `temperature`, `top_p`, etc.

        Returns:
            bool: whether the response is finished
        """
        if tool_type == 'function_call':
            options['functions'], options['function_call'] = self.functions, self.function_call or 'auto'
        else:
            options['tools'], options['tool_choice'] = self.tools, self.tool_choice or 'auto'
        show = lambda msg: print(self.display_role_content(msg))
        resp = self.getresponse(tool_type=tool_type, **options)
        if display: show(resp.message)
        while self.iswaiting() and maxturns != 0:
            # call api and update the result
            if tool_type != 'function_call':
                self.calltools(display=display)
            else:
                result, name, _ = self.callfunction()
                self.function(result, name)
                if display: show(self[-1])
            resp = self.getresponse(tool_type=tool_type, **options)
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
        model_url = "https://api.openai.com/v1/models"
        if self.api_base:
            model_url = os.path.join(self.api_base, 'models')
        elif self.base_url:
            model_url = os.path.join(self.base_url, 'v1/models')
        return valid_models(self.api_key, model_url, gpt_only=gpt_only)

    def get_curl(self, **options):
        """Print the curl command"""
        options = self._init_options(**options)
        api_key, chat_log, chat_url = self.api_key, self.chat_log, self.chat_url
        return curl_cmd_of_chat_completion(api_key, chat_url, chat_log, **options)
    
    def print_curl(self, **options):
        """Print the curl command"""
        print(self.get_curl(**options))
    
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
    def api_base(self):
        """Get base url"""
        return self._api_base
    
    @property
    def tool_type(self):
        """Get tool type"""
        return self._tool_type
    
    @property
    def functions(self):
        """Get functions"""
        return self._functions
    
    @property
    def function_call(self):
        """Get function call"""
        return self._function_call
    
    @property
    def tools(self):
        """Get tools"""
        if self.functions is not None:
            return [{'type':'function', 'function': func} for func in self.functions]
        return None
    
    @property
    def tool_choice(self):
        """Get tool choice"""
        return self._tool_choice

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
    def base_url(self, base_url:Union[None, str]):
        """Set base url"""
        if base_url:
            self.chat_url = base_url.rstrip('/') + '/v1/chat/completions'
        self._base_url = base_url
    
    @api_base.setter
    def api_base(self, api_base:Union[None, str]):
        """Set base url"""
        if api_base:
            self.chat_url = api_base.rstrip('/') + '/chat/completions'
        self._api_base = api_base

    @tool_type.setter
    def tool_type(self, tool_type:str):
        """Set tool type"""
        assert tool_type in ['tool_choice', 'function_call']
        self._tool_type = tool_type

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
    
    @tools.setter
    def tools(self, tools:List[Dict]):
        """Set tools"""
        assert isinstance(tools, list), "tools should be a list of dict"
        self._functions = [tool['function'] for tool in tools]

    @tool_choice.setter
    def tool_choice(self, tool_choice:str):
        """Set tool choice"""
        if tool_choice in ['auto', None, 'none']:
            self._tool_choice = tool_choice
        elif isinstance(tool_choice, str):
            self.tool_choice = {'name':tool_choice}
        elif isinstance(tool_choice, dict):
            assert 'name' in tool_choice
            self._tool_choice = tool_choice
    
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
        
    def _getresponse( self
                    , api_key:str
                    , chat_url:str
                    , msg:List[Dict]
                    , max_tries:int
                    , timeinterval:Union[float, int]
                    , **options)->Resp:
        resp, numoftries = None, 0
        # make requests
        while max_tries:
            try:
                # make API Call
                response = chat_completion(
                    api_key=api_key, messages=msg,
                    chat_url=chat_url, **options)
                resp = Resp(response)
                assert resp.is_valid(), resp.error_message
                break
            except Exception as e:
                max_tries -= 1
                numoftries += 1
                time.sleep(random.random() * timeinterval)
                print(f"Try again ({numoftries}):{e}\n")
        else:
            raise Exception("Request failed! Try using `debug_log()` to find out the problem " +
                            "or increase the `max_requests`.")
        return resp

    def _init_options( self
                     , tools:Union[None, List[Dict]]=None
                     , tool_choice:Union[None, str]=None
                     , tool_type:Union[str, None]=None
                     , functions:Union[None, List[Dict]]=None
                     , function_call:Union[None, str]=None
                     , **options):
        # initialize data
        if 'model' not in options: options['model'] = self.model
        # function call & tool call
        tool_type = tool_type or self.tool_type
        tool_choice, tools = tool_choice or self.tool_choice, tools or self.tools
        function_call, functions = function_call or self.function_call, functions or self.functions
        if tool_type == 'function_call':
            if function_call is not None:
                options['function_call'], options['functions'] = function_call, functions
        else:
            if tool_choice is not None:
                if tool_type != 'tool_choice':
                    logger.warning(f"Unknown tool type {tool_type}, use 'tool_choice' by default.")
                options['tool_choice'], options['tools'] = tool_choice, tools
        return options
    
async def _async_stream_responses( api_key:str
                                 , chat_url:str
                                 , chat_log:str
                                 , model:str
                                 , timeout:int=0
                                 , **options):
    """Post request asynchronously and stream the responses"""
    options.update({'model':model, 'messages':chat_log, 'stream':True})
    data = json.dumps(options)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key}
    async with aiohttp.ClientSession() as session:
        async with session.post(chat_url, headers=headers, data=data, timeout=timeout) as response:
            while True:
                line = await response.content.readline()
                if not line: break
                # strip the prefix of `data: {...}`
                strline = line.decode().lstrip('data:').strip()
                if strline == '[DONE]': break
                # skip empty line
                if not strline: continue
                # read the json string
                try:
                    # wrap the response
                    resp = Resp(json.loads(strline))
                    # deal with the message
                    if 'content' not in resp.delta: continue
                    yield resp
                    # stop if the response is finished
                    if resp.finish_reason == 'stop': break
                except Exception as e:
                    print(f"Error: {e}, line: {strline}")
                    break
