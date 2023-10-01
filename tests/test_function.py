# tests for function call

from chattool import Chat, generate_json_schema
import json, sys
from io import StringIO

# schema of functions
functions = [
{
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
}]

weatherinfo =  {
    "location": "Boston, MA",
    "temperature": "72",
    "forecast": ["sunny", "windy"],
    "unit":"celsius"
}
name2func = {
    'get_current_weather': lambda *kargs, **kwargs: weatherinfo
}

def test_function_call():
    chat = Chat("What's the weather like in Boston?")
    resp = chat.getresponse(functions=functions, function_call='auto')
    # TODO: wrap the response
    if resp.finish_reason == 'function_call':
        # test response from chat api
        parainfo = chat[-1]['function_call']
        func_name, func_args = parainfo['name'], json.loads(parainfo['arguments'])
        assert func_name == 'get_current_weather'
        assert 'location' in func_args and 'unit' in func_args
        # continue the chat
        chat.function(weatherinfo, func_name)
        chat.getresponse()
        # chat.save("testweather.json")
        chat.print_log()
    else:
        print("No function call found.")
        assert True

def test_function_call2():
    chat = Chat("What's the weather like in Boston?")
    chat.functions, chat.function_call = functions, 'auto'
    chat.name2func = name2func
    chat.autoresponse(max_requests=2)
    chat.print_log()

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
def mult(a:int, b:int=1) -> int:
    """
    This function multiplies two numbers.

    Args:
        a (int): The first number.
        b (int, optional): The second number. Defaults to 1.

    Returns:
        int: The product of the two numbers.
    """
    return a * b

def test_generate_docstring():
    functions = [generate_json_schema(add)]
    chat = Chat("find the sum of 784359345 and 345345345")
    chat.functions, chat.function_call = functions, 'auto'
    chat.name2func = {'add': add}
    chat.autoresponse(max_requests=2, display=True)
    chat.print_log()
    # use the setfuncs method
    chat = Chat("find the value of 124842 * 3423424")
    chat.setfuncs([add, mult]) # multi choice
    chat.autoresponse()
    chat.print_log()

def exec_python_code(code:str)->dict:
    """Execute the code and return the namespace or error message
    
    Args:
        code (str): code to execute

    Returns:
        dict: namespace or error message
    """
    try:
        namespace = {}
        exec(code, namespace)
        return namespace
    except Exception as e:
        return {'error': str(e)}