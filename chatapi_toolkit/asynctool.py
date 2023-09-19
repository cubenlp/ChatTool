import asyncio, aiohttp
import time, random, warnings, json, os
from typing import List, Dict, Union
from chatapi_toolkit import Chat, Resp, load_chats
import chatapi_toolkit
from tqdm.asyncio import tqdm

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
                    return await response.text()
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
        data = json.dumps(payload)
        response = await async_post( session=session
                                   , sem=sem
                                   , url=chat_url
                                   , data=data
                                   , headers=headers
                                   , max_requests=max_requests
                                   , timeinterval=timeinterval
                                   , timeout=timeout)
        if response is None:return False
        resp = Resp(json.loads(response))
        if not resp.is_valid():
            warnings.warn(f"Invalid response: {resp.error_message}")
            return False
        ## saving files
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
        if chatapi_toolkit.platform == "macos":
            responses = await tqdm.gather(tasks)
        else: # for windows and linux
            responses = await asyncio.gather(*tasks)
        for ind, cost in responses:
            costs[ind] = cost
        return costs

def async_chat_completion( chatlogs:Union[List[List[Dict]], str]
                         , chkpoint:str
                         , model:str='gpt-3.5-turbo'
                         , api_key:Union[str, None]=None
                         , chat_url:Union[str, None]=None
                         , max_requests:int=1
                         , ncoroutines:int=1
                         , timeout:int=0
                         , timeinterval:int=0
                         , clearfile:bool=False
                         , notrun:bool=False
                         , **options
                         ):
    """Asynchronous chat completion

    Args:
        chatlogs (Union[List[List[Dict]], str]): list of chat logs or chat message
        chkpoint (str): checkpoint file
        model (str, optional): model to use. Defaults to 'gpt-3.5-turbo'.
        api_key (Union[str, None], optional): API key. Defaults to None.
        max_requests (int, optional): maximum number of requests to make. Defaults to 1.
        ncoroutines (int, optional): number of coroutines. Defaults to 5.
        timeout (int, optional): timeout for the API call. Defaults to 0(no timeout).
        timeinterval (int, optional): time interval between two API calls. Defaults to 0.
        clearfile (bool, optional): whether to clear the checkpoint file. Defaults to False.
        notrun (bool, optional): whether to run the async process. It should be True
          when use in Jupyter Notebook. Defaults to False.

    Returns:
        List[Dict]: list of responses
    """
    # read chatlogs | use method from the Chat object
    chatlogs = [Chat(log).chat_log for log in chatlogs]
    if clearfile and os.path.exists(chkpoint):
        os.remove(chkpoint)
    if api_key is None:
        api_key = chatapi_toolkit.api_key
    assert api_key is not None, "API key is not provided!"
    if chat_url is None:
        chat_url = os.path.join(chatapi_toolkit.base_url, "v1/chat/completions")
    chat_url = chatapi_toolkit.request.normalize_url(chat_url)
    # run async process
    assert ncoroutines > 0, "ncoroutines must be greater than 0!"
    args = {
        "chatlogs": chatlogs,
        "chkpoint": chkpoint,
        "api_key": api_key,
        "chat_url": chat_url,
        "max_requests": max_requests,
        "ncoroutines": ncoroutines,
        "timeout": timeout,
        "timeinterval": timeinterval,
        "model": model,
        **options
    }
    if notrun: # when use in Jupyter Notebook
        return async_process_msgs(**args) # return the async object
    else:
        return asyncio.run(async_process_msgs(**args))