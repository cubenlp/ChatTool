# tests for function call

from chattool import Chat, generate_json_schema, exec_python_code
import json

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

def test_call_weather():
    chat = Chat("What's the weather like in Boston?")
    resp = chat.getresponse(functions=functions, function_call='auto', max_requests=3)
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

def test_auto_response():
    chat = Chat("What's the weather like in Boston?")
    chat.functions, chat.function_call = functions, 'auto'
    chat.name2func = name2func
    chat.autoresponse(max_requests=2)
    chat.print_log()
    chat.clear()
    # response with nonempty content
    chat.user("what is the result of 1+1, and What's the weather like in Boston?")
    chat.autoresponse(max_requests=2)

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
    functions = [generate_json_schema(add)]
    chat = Chat("find the sum of 784359345 and 345345345")
    chat.functions = functions
    chat.function_call = None # unset keyword equivalent to "auto"
    chat.function_call = 'none'
    chat.function_call = {'name':'add'}
    chat.function_call = 'add' # specify the function(convert to dict)
    chat.name2func = {'add': add} # dictionary of functions
    chat.function_call = 'auto' # auto decision
    # run until success: maxturns=-1
    chat.autoresponse(max_requests=3, display=True, timeinterval=2)
    # response should be finished
    chat.simplify()
    chat.print_log()
    # use the setfuncs method
    chat = Chat("find the value of 124842 * 3423424")
    chat.setfuncs([add, mult]) # multi choice
    chat.autoresponse(max_requests=3, timeinterval=2)
    chat.simplify() # simplify the chat log
    chat.print_log()
    # test multichoice
    chat.clear()
    chat.user("find the value of 23723 + 12312, and 23723 * 12312")
    chat.autoresponse(max_requests=3, timeinterval=2)

def test_mock_resp():
    chat = Chat("find the sum of 1235 and 3423")
    chat.setfuncs([add, mult])
    # mock result of the resp
    para = {'name': 'add', 'arguments': '{\n  "a": 1235,\n  "b": 3423\n}'}
    chat.assistant(content=None, function_call=para)
    chat.callfunction()
    chat.getresponse(max_requests=2)

def test_use_exec_function():
    chat = Chat("find the result of sqrt(121314)")
    chat.setfuncs([exec_python_code])
    chat.autoresponse(max_requests=2)
    
def test_find_permutation_group():
    pass

def test_interact_with_leandojo():
    pass

# debug area
# test_generate_docstring()
# test_function_call()
# test_function_call2()
