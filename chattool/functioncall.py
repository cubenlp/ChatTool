# Generate JSON Schema from a given function
# Json Schema: https://json-schema.org/understanding-json-schema/

from docstring_parser import parse
from typing import List, Dict

typemap = {
    'str': 'string',
    'int': 'integer',
    'float': 'number',
    'bool': 'boolean',
    'list': 'array',
    'dict': 'object',
    'tuple': 'array',
    'set': 'array',
    'None': 'null'
}

def generate_json_schema(func):
    """Generate JSON Schema from a given function

    Args:
        func (function): a function
    
    Returns:
        dict: JSON Schema
    """
    parsed_docstring = parse(func.__doc__)
    # template of JSON schema
    schema = {
        "name": func.__name__,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
    # generate description
    if parsed_docstring.short_description is not None:
        schema['description'] = parsed_docstring.short_description
        if parsed_docstring.long_description is not None:
            schema['description'] += '\n' + parsed_docstring.long_description
    # return info
    if parsed_docstring.returns is not None:
        returns = parsed_docstring.returns
        t = returns.type_name if returns.type_name is not None else 'object'
        if t in typemap: t = typemap[t]
        schema['returns'] = {'type':t}
        if returns.description is not None:
            schema['returns']['description']=returns.description
    # generate parameters
    for param in parsed_docstring.params:
        t = 'object' if param.type_name is None else param.type_name
        if t in typemap: t = typemap[t]
        schema["parameters"]["properties"][param.arg_name] = {
            "type": t,
            "description": param.description
        }
        if not param.is_optional:
            schema["parameters"]["required"].append(param.arg_name)
    return schema

def delete_dialogue_assist(chat_log:List[Dict]):
    """Delete the auto-generated dialogue"""
    ind = 0
    while ind < len(chat_log) - 1:
        log = chat_log[ind]
        if log['role'] == 'assistant' and 'function_call' in log:
            nextind = ind + 1
            nextlog = chat_log[nextind]
            if nextlog['role'] == 'function':
                chat_log.pop(nextind)
                chat_log.pop(ind)
        else:
            ind += 1
    return chat_log

def exec_python_code(code:str)->dict:
    """Execute the code and return the namespace or error message
    
    Args:
        code (str): code to execute

    Returns:
        dict: namespace or error message
    """
    try:
        globalspace, currentspace, newspace = globals().copy(), globals().copy(), {}
        exec(code, globalspace)
        for key, val in globalspace.items():
            if key not in currentspace:
                newspace[key] = str(val)
        return newspace
    except Exception as e:
        return {'error': str(e)}