import json, warnings, os
from typing import List, Dict, Union, Callable, Any
from .chattype import Chat
import tqdm

def load_chats( checkpoint:str):
    """Load chats from a checkpoint file
    
    Args:
        checkpoint (str): path to the checkpoint file

    Returns:
        list: chats
    """
    # if the checkpoint file does not exist, return empty list
    if not os.path.exists(checkpoint):
        # warnings.warn(f"checkpoint file {checkpoint} does not exist")
        return []
    # load chats from the checkpoint file
    with open(checkpoint, 'r', encoding='utf-8') as f:
        txts = f.read().strip().split('\n')
    ## empty file
    if len(txts) == 1 and txts[0] == '': return []
    # get the chatlogs
    logs = [json.loads(txt) for txt in txts]
    chat_size, chatlogs = 1, [None]
    for log in logs:
        idx = log['index']
        if idx >= chat_size: # extend chatlogs
            chatlogs.extend([None] * (idx - chat_size + 1))
            chat_size = idx + 1
        chatlogs[idx] = log['chat_log']
    # check if there are missing chatlogs
    if None in chatlogs:
        warnings.warn(f"checkpoint file {checkpoint} has unfinished chats")
    # return Chat class
    return [Chat(chat_log) if chat_log is not None else None for chat_log in chatlogs]

def process_chats( data:List[Any]
                 , data2chat:Callable[[Any], Chat]
                 , checkpoint:str
                 , clearfile:bool=False
                 , isjupyter:bool=False):
    """Process chats and save to a checkpoint file(non-asyncio version)
    
    Args:
        data (List[Any]): data to be processed
        data2chat (Callable[[Any], Chat]): function to convert data to Chat
        checkpoint (str): path to the checkpoint file
        clearfile (bool, optional): whether to clear the checkpoint file. Defaults to False.
        isjupyter (bool, optional): whether to use tqdm in Jupiter Notebook. Defaults to False.

    Returns:
        list: chats or last messages of chats
    """
    if clearfile and os.path.exists(checkpoint):
        # Warning: You are about to delete the checkpoint file
        os.system(f"rm {checkpoint}")
    ## load chats from the checkpoint file
    chats = load_chats(checkpoint)
    if len(chats) > len(data):
        warnings.warn(f"checkpoint file {checkpoint} has more chats than the data to be processed")
        return chats[:len(data)]
    chats.extend([None] * (len(data) - len(chats)))
    ## process chats
    tq = tqdm.tqdm if not isjupyter else tqdm.notebook.tqdm
    for i in tq(range(len(data))):
        if chats[i] is not None: continue
        chat = data2chat(data[i])
        chat.save(checkpoint, mode='a', index=i)
        chats[i] = chat
    return chats