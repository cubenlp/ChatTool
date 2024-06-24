from chattool import Chat

def test_simple_chat():
    chat = Chat()
    chat.print_curl() # empty chat
    chat.user("Hello!")
    chat.print_curl() # user message
    curl_cmd = chat.get_curl()
    resp = chat.getresponse()
    resp_curl = resp.get_curl()
    resp.print_curl()
    assert curl_cmd == resp_curl

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

def test_tool_call():
    chat = Chat()
    chat.user("find the sum of 784359345 and 345345345")
    chat.print_curl(use_env_key=True)
    chat.settools([add])
    chat.print_curl()
    chat.tool_type = 'function_call'
    chat.function_call = 'auto'
    chat.print_curl()
    curl_cmd = chat.get_curl()
    resp = chat.getresponse()
    resp_curl = resp.get_curl()
    resp.print_curl()
    assert curl_cmd == resp_curl