# The object that stores the chat log

from typing import List, Dict, Union

def default_prompt(msg:str):
    """Default prompt message for the API call

    Args:
        msg (str): prompt message

    Returns:
        List[Dict]: default prompt message
    """
    return [{"role": "user", "content": msg},]


class Chat():
    def __init__(self, msg:Union[List[Dict], None, str]) -> None:
        if msg is None:
            self._chat_log = []
        elif isinstance(msg, str):
            self._chat_log = default_prompt(msg)
        elif isinstance(msg, list):
            self._chat_log = msg
        else:
            raise ValueError("msg should be a list of dict or None")
    
    def add(self, role, msg, copy:bool=False):
        assert role in ['user', 'assistant', 'system'], "role should be 'user', 'assistant' or 'system'"
        if isinstance(msg, str):
            self._chat_log.append({"role": role, "content": msg})
        else:
            raise ValueError("msg should be a string")
        return self if not copy else self.copy()

    def user(self, msg, copy:bool=False):
        """User message"""
        return self.add('user', msg, copy=copy)
    
    def assistant(self, msg, copy:bool=False):
        """Assistant message"""
        return self.add('assistant', msg, copy=copy)
    
    def system(self, msg, copy:bool=False):
        """System message"""
        return self.add('system', msg, copy=copy)
    
    def clear(self):
        """Clear the chat log"""
        self._chat_log = []
    
    def copy(self):
        """Copy the chat log"""
        return Chat(self._chat_log.copy())
    
    def print_log(self, sep: Union[str, None]=None):
        if sep is None:
            sep = '\n' + '-'*15 + '\n'
        for d in self._chat_log:
            print(sep, d['role'], sep, d['content'])
    
    @property
    def history(self):
        """Chat history"""
        return self._chat_log
    
    def pop(self):
        """Pop the last message"""
        return self._chat_log.pop()

    def __len__(self):
        """Length of the chat log"""
        return len(self._chat_log)
    
    def __repr__(self) -> str:
        return f"<Chat with {len(self)} messages>"
    
    def __str__(self) -> str:
        return f"{self.history}"
