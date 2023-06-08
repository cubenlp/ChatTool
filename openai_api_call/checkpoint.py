import json, warnings, os
from typing import List, Dict, Union, Callable
from .chattool import Chat

def load_chats( checkpoint:str
              , sep='\n'
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
        msgs = [None] * len(chatlogs)
        for i, chat in enumerate(chatlogs):
            if chat is None: continue
            msgs[i] = chat[-1]['content'] if len(chat) else ""
        return msgs
    # chat log only
    if chat_log_only: return chatlogs
    # return Chat class
    return [Chat(chatlog) if chatlog is not None else None for chatlog in chatlogs]

def process_chats( msgs:List[str]
                 , msg2chat:Callable[[str], Chat]
                 , checkpoint:str
                 , sep:str='\n'
                 , last_message_only:bool=False
                 , clearfile:bool=False):
    """Process chats and save to a checkpoint file
    
    Args:
        msgs (List[str]): messages
        msg2chat (Callable[[str], Chat]): function to convert a message to a chat
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
    if len(chats) > len(msgs):
        warnings.warn(f"checkpoint file {checkpoint} has more chats than the messages")
        return chats[:len(msgs)]
    chats.extend([None] * (len(msgs) - len(chats)))
    ## process chats
    for i, msg in enumerate(msgs):
        if chats[i] is not None: continue
        chat = msg2chat(msg)
        chat.save(checkpoint, mode='a', end=sep)
        chats[i] = chat
    if last_message_only:
        return [chat[-1] for chat in chats]
    return chats