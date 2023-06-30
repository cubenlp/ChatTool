# test for fucntion description

from openai_api_call import func2desc
import json

def usage_status(api_key:str, duration:int=99):
    """Get usage status
    
    Args:
        api_key (str): API key
        duration (int, optional): duration to check. Defaults to 99, which is the maximum duration.
    
    Returns:
        Tuple[float, float, List[float]]: total storage, total usage, daily costs
    """
    return

def get_current_weather(location:str, unit:str="fahrenheit"):
    """Get the current weather in a given location
    
    Args:
        location (str): The city and state, e.g. San Francisco, CA
        unit (str, optional): The temperature unit to use. Infer this from the users location. Defaults to "fahrenheit".

    Returns:
        str: The current weather
    """
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)

def test_funcdesc():
    # generate docs for `usage_status`
    func = func2desc(usage_status)
    assert func['name'] == "usage_status"
    assert func == {'name': 'usage_status',
                    'description': 'Get usage status\n',
                    'parameters': {'type': 'object',
                    'properties': {'api_key': {'type': str, 'description': ''},
                                    'duration': {'type': int, 'description': ''}},
                    'required': ['api_key', 'duration']}}
    func = func2desc(usage_status, parabydoc=True)
    assert func == {'name': 'usage_status',
                    'description': 'Get usage status\n',
                    'parameters': {'type': 'object',
                    'properties': {'api_key': {'type': 'str', 'description': 'API key'},
                                    'duration': {'type': 'int', 'description':
                                                 'duration to check. Defaults to 99, which is the maximum duration.'}},
                    'required': ['api_key', 'duration']}}
    # generate docs for `get_current_weather`
    func = func2desc(get_current_weather)
    assert func['name'] == "get_current_weather"
    assert func == {'name': 'get_current_weather',
                    'description': 'Get the current weather in a given location\n',
                    'parameters': {'type': 'object',
                    'properties': {'location': {'type': str, 'description': ''},
                                    'unit': {'type': str, 'description': ''}},
                    'required': ['location', 'unit']}}

    # generate docs for `get_current_weather` with default values
    func = func2desc(get_current_weather, required=['location'])
    assert func['name'] == "get_current_weather"
    assert func['parameters']['required'] == ['location']