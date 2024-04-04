# Request functions for chattool
# Documentation: https://platform.openai.com/docs/api-reference

from typing import List, Dict, Union
import requests, json, os
from urllib.parse import urlparse, urlunparse
import warnings

def is_valid_url(url: str) -> bool:
    """Check if the given URL is valid.

    Args:
        url (str): The URL to be checked.

    Returns:
        bool: True if the URL is valid; otherwise False.
    """
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])

def normalize_url(url: str) -> str:
    """Normalize the given URL to a canonical form.

    Args:
        url (str): The URL to be normalized.

    Returns:
        str: The normalized URL.

    Examples:
        >>> normalize_url("http://api.example.com")
        'http://api.example.com'

        >>> normalize_url("api.example.com")
        'https://api.example.com'
    """
    url = url.replace("\\", '/') # compat to windows
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        # If no scheme is specified, default to https protocol.
        parsed_url = parsed_url._replace(scheme="https")
    return urlunparse(parsed_url).replace("///", "//")

def chat_completion( api_key:str
                   , chat_url:str
                   , messages:List[Dict]
                   , model:str
                   , timeout:int = 0
                   , **options) -> Dict:
    """Chat completion API call
    Request url: https://api.openai.com/v1/chat/completions
    
    Args:
        apikey (str): API key
        chat_url (str): chat url
        messages (List[Dict]): prompt message
        model (str): model to use
        **options : options inherited from the `openai.ChatCompletion.create` function.
    
    Returns:
        Dict: API response
    """
    # request data
    payload = {
        "model": model,
        "messages": messages,
        **options
    }
    # request headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key
    }
    chat_url = normalize_url(chat_url)
    # get response
    if timeout <= 0: timeout = None
    response = requests.post(
        chat_url, headers=headers, 
        data=json.dumps(payload), timeout=timeout)
    if response.status_code != 200:
        raise Exception(response.text)
    return response.json()

def valid_models(api_key:str, model_url:str, gpt_only:bool=True):
    """Get valid models
    Request url: https://api.openai.com/v1/models

    Args:
        api_key (str): API key
        base_url (str): base url
        gpt_only (bool, optional): whether to return only GPT models. Defaults to True.

    Returns:
        List[str]: list of valid models
    """
    headers = {
        "Authorization": "Bearer " + api_key,
    }
    model_response = requests.get(normalize_url(model_url), headers=headers)
    if model_response.status_code == 200:
        data = model_response.json()
        model_list = [model.get("id") for model in data.get("data")]
        return [model for model in model_list if "gpt" in model] if gpt_only else model_list
    else:
        raise Exception(model_response.text)

def loadfile(api_key:str, base_url:str, file:str, purpose:str='fine-tune'):
    """Upload a file that can be used across various endpoints/features. 
    Currently, the size of all the files uploaded by one organization can be up to 1 GB.
    """
    assert purpose == 'fine-tune', "Currently only support fine-tune purpose"
    headers = {"Authorization": "Bearer " + api_key}
    loadfile_url = normalize_url(os.path.join(base_url, "v1/files"))
    resp = requests.post(loadfile_url, headers=headers, data={"purpose": purpose}, files={"file": open(file, "rb")})
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(resp.text)

def filelist(api_key:str, base_url:str):
    """"Returns a list of files that belong to the user's organization"""
    headers = {"Authorization": "Bearer " + api_key}
    filelist_url = normalize_url(os.path.join(base_url, "v1/files"))
    resp = requests.get(filelist_url, headers=headers)
    if resp.status_code == 200:
        return resp.json()['data']
    else:
        raise Exception(resp.text)

def filecontent(api_key:str, base_url:str, fileid:str):
    """Returns the contents of the specified file"""
    headers = {
        "Authorization": "Bearer " + api_key,
    }
    fileurl = normalize_url(os.path.join(base_url, "v1/files", fileid, "content"))
    resp = requests.get(fileurl, headers=headers)
    if resp.status_code == 200:
        return [json.loads(msg) for msg in resp.content.decode().split('\n') if msg]
    else:
        raise Exception(resp.text)

def deletefile(api_key:str, base_url:str, fileid:str):
    """Delete file"""
    headers = {"Authorization": "Bearer " + api_key}
    fileurl = normalize_url(os.path.join(base_url, "v1/files", fileid))
    resp = requests.delete(fileurl, headers=headers)
    if resp.status_code == 200:
        return resp.json()['deleted']
    else:
        warnings.warn(resp.text)
        return False

def create_finetune_job( api_key:str
                       , base_url:str
                       , model:str
                       , trainingid:str
                       , validationid:Union[str, None] = None
                       , suffix:Union[str, None] = None
                       , **hyperparameters):
    """Creates a job that fine-tunes a specified model from a given dataset.
    Response includes details of the enqueued job including job status 
    and the name of the fine-tuned models once complete.
    
    Args:
        api_key (str): API key
        base_url (str): base url
        model (str): model to use
        trainingid (str): training file id
        validationid (Union[str, None], optional): validation file id. Defaults to None.
        **hyperparameters : hyperparameters to use, example: n_epochs=5
    """
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json"
    }
    createjob_url = normalize_url(os.path.join(base_url, "v1/fine_tuning/jobs"))
    payload = {
        "model": model,
        "training_file": trainingid,
    }
    if validationid is not None:
        payload["validation_file"] = validationid
    if suffix is not None:
        payload["suffix"] = suffix
    if hyperparameters:
        payload["hyperparameters"] = hyperparameters
    resp = requests.post(createjob_url, headers=headers, data=json.dumps(payload))
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(resp.text)

def list_finetune_job(api_key:str, base_url:str, limit:int=0):
    """List your organization's fine-tuning jobs."""
    headers = {"Authorization": "Bearer " + api_key}
    if limit == 0: # default to 20
        listjob_url = normalize_url(os.path.join(base_url, "v1/fine_tuning/jobs"))
    else:
        listjob_url = normalize_url(os.path.join(base_url, "v1/fine_tuning/jobs?limit=" + str(limit)))
    resp = requests.get(listjob_url, headers=headers)
    if resp.status_code == 200:
        return resp.json()['data']
    else:
        raise Exception(resp.text)

def retrievejob(api_key:str, base_url:str, jobid:str):
    """Get info about a fine-tuning job"""
    headers = {"Authorization": "Bearer " + api_key}
    retrieve_url = normalize_url(os.path.join(base_url, "v1/fine_tuning/jobs", jobid))
    resp = requests.get(retrieve_url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(resp.text)
    
def listevents(api_key:str, base_url:str, jobid:str, limit:int=0):
    """Get status updates for a fine-tuning job"""
    headers = {"Authorization": "Bearer " + api_key}
    if limit == 0: # default to 20
        listevents_url = normalize_url(os.path.join(base_url, "v1/fine_tuning/jobs", jobid, "events"))
    else:
        listevents_url = normalize_url(os.path.join(base_url, "v1/fine_tuning/jobs", jobid, "events?limit=" + str(limit)))
    resp = requests.get(listevents_url, headers=headers)
    if resp.status_code == 200:
        return resp.json()['data']
    else:
        raise Exception(resp.text)
    
def canceljob(api_key:str, base_url:str, jobid:str):
    """Immediately cancel a fine-tune job."""
    headers = {"Authorization": "Bearer " + api_key}
    cancel_url = normalize_url(os.path.join(base_url, "v1/fine_tuning/jobs", jobid, "cancel"))
    resp = requests.post(cancel_url, headers=headers)
    if resp.status_code == 200:
        return resp.json()['data']
    else:
        raise Exception(resp.text)

def deletemodel(api_key:str, base_url:str, modelid:str):
    """Delete a fine-tuned model. 
    You must have the Owner role in your organization to delete a model"""
    headers = {"Authorization": "Bearer " + api_key}
    delete_url = normalize_url(os.path.join(base_url, "v1/models/", modelid))
    resp = requests.delete(delete_url, headers=headers)
    if resp.status_code == 200:
        return resp.json()['deleted']
    else:
        warnings.warn(resp.text)
        return False