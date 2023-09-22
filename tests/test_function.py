# tests for function call

from chattool import Chat
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