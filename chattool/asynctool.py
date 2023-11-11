import asyncio, aiohttp
import time, random, warnings, json, os
from typing import List, Dict, Union, Callable
from chattool import Chat, Resp, load_chats
import chattool
import tqdm.asyncio

async def async_post( session
                    , sem
                    , url
                    , data:str
                    , headers:Dict
                    , max_requests:int=1
                    , timeinterval=0
                    , timeout=0):
    """Asynchronous post request

    Args:
        session : aiohttp session
        sem : semaphore
        url (str): chat completion url
        data (str): payload of the request
        headers (Dict): request headers
        max_requests (int, optional): maximum number of requests to make. Defaults to 1.
        timeinterval (int, optional): time interval between two API calls. Defaults to 0.
        timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
    
    Returns:
        str: response text
    """
    async with sem:
        ntries = 0
        while max_requests > 0:
            try:    
                async with session.post(url, headers=headers, data=data, timeout=timeout) as response:
                    resp = await response.text()
                    resp = Resp(json.loads(resp))
                    assert resp.is_valid(), resp.error_message
                    return resp
            except Exception as e:
                max_requests -= 1
                ntries += 1
                time.sleep(random.random() * timeinterval)
                print(f"Request Failed({ntries}):{e}")
        else:
            warnings.warn("Maximum number of requests reached!")
            return None    
    
async def async_process_msgs( chatlogs:List[List[Dict]]
                            , chkpoint:str
                            , api_key:str
                            , chat_url:str
                            , max_requests:int=1
                            , ncoroutines:int=1
                            , timeout:int=0
                            , timeinterval:int=0
                            , max_tokens:Union[Callable, None]=None
                            , **options
                            )->List[bool]:
    """Process messages asynchronously

    Args:
        chatlogs (List[List[Dict]]): list of chat logs
        chkpoint (str): checkpoint file
        api_key (Union[str, None], optional): API key. Defaults to None.
        max_requests (int, optional): maximum number of requests to make. Defaults to 1.
        ncoroutines (int, optional): number of coroutines. Defaults to 5.
        timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
        timeinterval (int, optional): time interval between two API calls. Defaults to 0.

    Returns:
        List[bool]: list of responses
    """
    # load from checkpoint
    chats = load_chats(chkpoint, withid=True) if os.path.exists(chkpoint) else []
    chats.extend([None] * (len(chatlogs) - len(chats)))
    costs = [0] * len(chatlogs)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key
    }
    ncoroutines += 1 # add one for the main coroutine
    sem = asyncio.Semaphore(ncoroutines)
    locker = asyncio.Lock()

    async def chat_complete(ind, locker, chatlog, chkpoint, **options):
        payload = {"messages": chatlog}
        payload.update(options)
        if max_tokens is not None:
            payload['max_tokens'] = max_tokens(chatlog)
        data = json.dumps(payload)
        resp = await async_post( session=session
                               , sem=sem
                               , url=chat_url
                               , data=data
                               , headers=headers
                               , max_requests=max_requests
                               , timeinterval=timeinterval
                               , timeout=timeout)
        ## saving files
        if resp is None: return 0, 0
        chatlog.append(resp.message)
        chat = Chat(chatlog)
        async with locker: # locker | not necessary for normal IO
            chat.savewithid(chkpoint, chatid=ind)
        return ind, resp.cost()

    async with sem, aiohttp.ClientSession() as session:
        tasks = []
        for ind, chatlog in enumerate(chatlogs):
            if chats[ind] is not None: # skip completed chats
                continue
            tasks.append(
                asyncio.create_task(
                    chat_complete( ind=ind
                                 , locker=locker
                                 , chatlog=chatlog
                                 , chkpoint=chkpoint
                                 , **options)))
        try: # for mac or linux
            responses = await tqdm.asyncio.tqdm.gather(tasks)
        except TypeError: # for windows or linux 
            responses = await tqdm.asyncio.tqdm.gather(*tasks)
        for ind, cost in responses:
            costs[ind] = cost
        return costs

def async_chat_completion( msgs:Union[List[List[Dict]], str]
                         , chkpoint:str
                         , model:str='gpt-3.5-turbo'
                         , api_key:Union[str, None]=None
                         , chat_url:Union[str, None]=None
                         , max_requests:int=1
                         , ncoroutines:int=1
                         , nproc:int=1
                         , timeout:int=0
                         , timeinterval:int=0
                         , clearfile:bool=False
                         , notrun:bool=False
                         , msg2log:Union[Callable, None]=None
                         , data2chat:Union[Callable, None]=None
                         , max_tokens:Union[Callable, int, None]=None
                         , **options
                         ):
    """Asynchronous chat completion

    Args:
        msgs (Union[List[List[Dict]], str]): list of chat logs or chat message
        chkpoint (str): checkpoint file
        model (str, optional): model to use. Defaults to 'gpt-3.5-turbo'.
        api_key (Union[str, None], optional): API key. Defaults to None.
        max_requests (int, optional): maximum number of requests to make. Defaults to 1.
        ncoroutines (int, optional): (Deprecated)number of coroutines. Defaults to 1.
        nproc (int, optional): number of coroutines. Defaults to 1.
        timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
        timeinterval (int, optional): time interval between two API calls. Defaults to 0.
        clearfile (bool, optional): whether to clear the checkpoint file. Defaults to False.
        notrun (bool, optional): whether to run the async process. It should be True
          when use in Jupyter Notebook. Defaults to False.
        msg2log (Union[Callable, None], optional): function to convert message to chat log.
            Defaults to None.
        data2chat (Union[Callable, None], optional): function to convert data to Chat object.
            Defaults to None.
        max_tokens (Union[Callable, int, None], optional): function to calculate the maximum
            number of tokens for the API call. Defaults to None.

    Returns:
        List[Dict]: list of responses
    """
    # convert chatlogs
    if data2chat is not None:
        msg2log = lambda data: data2chat(data).chat_log
    elif msg2log is None: # By default, use method from the Chat object
        msg2log = lambda data: Chat(data).chat_log
    # use nproc instead of ncoroutines
    nproc = max(nproc, ncoroutines)
    chatlogs = [msg2log(log) for log in msgs]
    if clearfile and os.path.exists(chkpoint):
        os.remove(chkpoint)
    if api_key is None:
        api_key = chattool.api_key
    assert api_key is not None, "API key is not provided!"
    if chat_url is None:
        chat_url = os.path.join(chattool.base_url, "v1/chat/completions")
    chat_url = chattool.request.normalize_url(chat_url)
    # run async process
    assert ncoroutines > 0, "ncoroutines must be greater than 0!"
    if isinstance(max_tokens, int):
         max_tokens = lambda chatlog: max_tokens
    args = {
        "chatlogs": chatlogs,
        "chkpoint": chkpoint,
        "api_key": api_key,
        "chat_url": chat_url,
        "max_requests": max_requests,
        "ncoroutines": nproc,
        "timeout": timeout,
        "timeinterval": timeinterval,
        "model": model,
        "max_tokens": max_tokens,
        **options
    }
    if notrun: # when use in Jupyter Notebook
        return async_process_msgs(**args) # return the async object
    else:
        return asyncio.run(async_process_msgs(**args))