# tests for function call

from chattool import Chat, generate_json_schema, exec_python_code
import json

# schema of functions
tools = [
    {
        "type": "function",
        "function":{
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location", "unit"],
            },
        }
    }
]
weatherinfo =  {
    "location": "Boston, MA",
    "temperature": "72",
    "forecast": ["sunny", "windy"],
    "unit":"celsius"
}
name2func = {
    'get_current_weather': lambda *kargs, **kwargs: weatherinfo
}

def test_call_weather():
    chat = Chat("What's the weather like in Boston?")
    resp = chat.getresponse(tools=tools, tool_choice='auto', max_tries=3)
    if resp.finish_reason == 'tool_calls':
        last_tool = chat[-1]['tool_calls'][0] # get the last tool call
        parainfo, tool_call_id = last_tool['function'], last_tool['id']
        tool_name, tool_args = parainfo['name'], json.loads(parainfo['arguments'])
        assert tool_name == 'get_current_weather'
        assert 'location' in tool_args and 'unit' in tool_args
        # continue the chat
        # tool call result: weatherinfo
        chat.tool(weatherinfo, tool_name, tool_call_id)
        chat.getresponse()
        chat.print_log()
    else:
        print("No function call found.")
        assert True

def test_auto_response():
    chat = Chat("What's the weather like in Boston?")
    chat.tools, chat.tool_choice = tools, 'auto'
    chat.name2func = name2func
    chat.autoresponse(max_tries=2, display=True)
    chat.print_log()
    newchat = chat.deepcopy()
    newchat.clear()
    # response with nonempty content
    newchat.user("what is the result of 1+1, and What's the weather like in Boston?")
    newchat.autoresponse(max_tries=2, display=True)

# generate docstring from functions
def add(a: int, b: int) -> int:
    """
    This function adds two numbers.

    Parameters:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The sum of the two numbers.
    """
    return a + b

# with optional parameters
def mult(a:int, b:int) -> int:
    """This function multiplies two numbers.
    It is a useful calculator!

    Args:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The product of the two numbers.
    """
    return a * b

def test_add_and_mult():
    tools = [{
    'type':'function', 
    'function': generate_json_schema(tool)} for tool in [add, mult]]
    chat = Chat("find the sum of 784359345 and 345345345")
    chat.tools = tools
    chat.tool_choice = None # unset keyword equivalent to "auto"
    chat.tool_choice = 'none'
    chat.tool_choice = {'name':'add'}
    chat.tool_choice = 'add' # specify the function(convert to dict)
    chat.tools = tools
    chat.name2func = {'add': add} # dictionary of functions
    chat.tool_choice = 'auto' # auto decision
    # run until success: maxturns=-1
    chat.autoresponse(max_tries=3, display=True, timeinterval=2)
    # response should be finished
    chat.simplify()
    chat.print_log()
    # use the setfuncs method
    chat2 = Chat("find the value of 124842 * 3423424")
    chat2.settools([add, mult]) # multi choice
    chat2.autoresponse(max_tries=3, display=True, timeinterval=2)
    chat2.simplify() # simplify the chat log
    chat2.print_log()
    # test multichoice
    chat3 = chat2.deepcopy()
    chat3.clear()
    chat3.user("find the value of 23723 + 12312, and 23723 * 12312")
    chat3.autoresponse(max_tries=3, display=True, timeinterval=2)
    # test multichoice 
    chat4 = chat2.deepcopy()
    chat4.clear()
    chat4.user("find the value of (23723 * 1322312 ) + 12312")
    chat4.autoresponse(max_tries=3, display=True, timeinterval=2)


def test_use_exec_function():
    chat = Chat("find the result of sqrt(121314)")
    chat.settools([exec_python_code])
    chat.autoresponse(max_tries=2, display=True)
    
def test_find_permutation_group():
    pass

def test_interact_with_leandojo():
    pass

# debug area
# test_generate_docstring()
# test_function_call()
# test_function_call2()
