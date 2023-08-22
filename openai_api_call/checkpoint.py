import json, warnings, os
from typing import List, Dict, Union, Callable, Any
from .chattool import Chat
import tqdm

def load_chats( checkpoint:str
              , last_message_only:bool=False
              , chat_log_only:bool=False
              , withid:bool=False):
    """Load chats from a checkpoint file
    
    Args:
        checkpoint (str): path to the checkpoint file
        sep (str, optional): separator of chats. Defaults to '\n'.
        last_message_only (bool, optional): whether to return the last message of each chat. Defaults to False.
        chat_log_only (bool, optional): whether to return the chat log only. Defaults to False.

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
    chats = [json.loads(txt) for txt in txts]
    ## chats with chatid
    if withid:
        chat_size, chatlogs = 1, [None]
        for chat in chats:
            idx = chat['chatid']
            if idx >= chat_size: # extend chatlogs
                chatlogs.extend([None] * (idx - chat_size + 1))
                chat_size = idx + 1
            chatlogs[idx] = chat['chatlog']
    else: ## chats without chatid
        chatlogs = chats
    # return the last message of chats only
    if last_message_only:
        data = [None] * len(chatlogs)
        for i, log in enumerate(chatlogs):
            if log is None: continue
            data[i] = log[-1]['content'] if len(log) else "" # empty log, like []
        return data
    # return chat log only
    if chat_log_only: return chatlogs
    # return Chat class
    return [Chat(chatlog) if chatlog is not None else None for chatlog in chatlogs]

def process_chats( data:List[Any]
                 , data2chat:Callable[[Any], Chat]
                 , checkpoint:str
                 , cleanstart:bool=False
                 , isjupyter:bool=False):
    """Process chats and save to a checkpoint file(non-asyncio version)
    
    Args:
        data (List[Any]): data to be processed
        data2chat (Callable[[Any], Chat]): function to convert data to Chat
        checkpoint (str): path to the checkpoint file
        cleanstart (bool, optional): whether to use the checkpoint file before processing. Defaults to False.
        isjupyter (bool, optional): whether to use tqdm in Jupiter Notebook. Defaults to False.

    Returns:
        list: chats or last messages of chats
    """
    if cleanstart and os.path.exists(checkpoint):
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
        chat.save(checkpoint, mode='a')
        chats[i] = chat
    return chats