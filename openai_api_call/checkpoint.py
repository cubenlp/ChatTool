import json, warnings, os
from typing import List, Dict, Union, Callable, Any
from .chattool import Chat
from tqdm import tqdm

def load_chats( checkpoint:str
              , sep:str='\n'
              , last_message_only:bool=False
              , chat_log_only:bool=False):
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
        txts = f.read().strip().split(sep)
    if len(txts) == 1 and txts[0] == '': return []
    chats = [json.loads(txt) for txt in txts]
    if 'chatid' in chats[0]: # chats with chatid
        chat_size = chats[-1]['chatid']
        chatlogs = [None] * chat_size
        for chat in chats:
            idx = chat['chatid']
            if idx >= chat_size:
                chatlogs.extend([None] * (idx - chat_size + 1))
                chat_size = idx + 1
            chatlogs[idx] = chat['chatlog']
    else: # chats without chatid
        chatlogs = chats
    # last message of chats only
    if last_message_only:
        data = [None] * len(chatlogs)
        for i, chat in enumerate(chatlogs):
            if chat is None: continue
            data[i] = chat[-1]['content'] if len(chat) else ""
        return data
    # chat log only
    if chat_log_only: return chatlogs
    # return Chat class
    return [Chat(chatlog) if chatlog is not None else None for chatlog in chatlogs]

def process_chats( data:List[Any]
                 , data2chat:Callable[[Any], Chat]
                 , checkpoint:str
                 , sep:str='\n'
                 , last_message_only:bool=False
                 , clearfile:bool=False):
    """Process chats and save to a checkpoint file
    
    Args:
        data (List[Any]): data to be processed
        data2chat (Callable[[Any], Chat]): function to convert data to Chat
        checkpoint (str): path to the checkpoint file
        sep (str, optional): separator of chats. Defaults to '\n'.
        last_message_only (bool, optional): whether to return the last message of each chat. Defaults to False.
        clearfile (bool, optional): whether to clear the checkpoint file. Defaults to False.

    Returns:
        list: chats or last messages of chats
    """
    if clearfile and os.path.exists(checkpoint):
        # Warning: You are about to delete the checkpoint file
        os.system(f"rm {checkpoint}")
    ## load chats from the checkpoint file
    chats = load_chats(checkpoint, sep=sep)
    if len(chats) > len(data):
        warnings.warn(f"checkpoint file {checkpoint} has more chats than the messages")
        chats = chats[:len(data)]
        return [chat[-1] for chat in chats] if last_message_only else chats
        
    chats.extend([None] * (len(data) - len(chats)))
    ## process chats
    for i in tqdm(range(len(data))):
        if chats[i] is not None: continue
        chat = data2chat(data[i])
        chat.save(checkpoint, mode='a', end=sep)
        chats[i] = chat
    if last_message_only:
        return [chat[-1] for chat in chats]
    return chats