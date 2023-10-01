# Fine tune the model on the dataset
from .request import (
    loadfile, deletefile, filelist, filecontent,
    create_finetune_job, list_finetune_job, retrievejob,
    listevents, canceljob, deletemodel, valid_models
)
from typing import Union
import chattool

class FineTune():
    def __init__( self
                , api_key:Union[None, str] = None
                , base_url:Union[None, str] = None
                , model:Union[None, str] = None
                , modelid:Union[None, str] = None
                , jobid:Union[None, str] = None
                , trainingid:Union[None, str] = None
                , validationid:Union[None, str] = None
                 ) -> None:
        self._api_key = api_key or chattool.api_key
        self._base_url = base_url or chattool.base_url
        self._model = model or 'gpt-3.5-turbo'
        self._modelid, self._jobid = modelid, jobid
        self._trainingid, self._validationid = trainingid, validationid

    def training_file(self, filename:str):
        """Upload a training file to the API."""
        resp = loadfile(self.api_key, self.base_url, filename)
        self.trainingid = resp['id']
        return resp

    def validation_file(self, filename:str):
        """Upload a validation file to the API."""
        resp = loadfile(self.api_key, self.base_url, filename)
        self.validationid = resp['id']
        return resp

    def list_files(self):
        """List all files."""
        return filelist(self.api_key, self.base_url)
    
    def delete_file(self, fileid:str):
        """Delete a file."""
        return deletefile(self.api_key, self.base_url, fileid)
    
    def file_content(self, fileid:str):
        """Get the content of a file."""
        return filecontent(self.api_key, self.base_url, fileid)
    
    def create_job( self
                  , model:Union[str, None]=None
                  , trainingid:Union[str, None]=None
                  , validationid:Union[str, None]=None
                  , suffix:Union[str, None]=None
                  , **hyperparameters):
        """Create a fine-tuning job."""
        if model is None:model = self.model
        if trainingid is None:trainingid = self.trainingid
        assert trainingid is not None, "trainingid must be specified"
        if validationid is None:validationid = self.validationid
        args = {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": model,
            "trainingid": trainingid,
            "suffix": suffix
            **hyperparameters
        }
        if validationid is not None:args['validationid'] = validationid
        resp = create_finetune_job(**args)
        self.jobid = resp['id']

    def list_jobs(self, limit:int=0):
        """List your organization's fine-tuning jobs."""
        return list_finetune_job(self.api_key, self.base_url, limit)
    
    def retrieve_job(self, jobid:Union[str, None]=None):
        """Get info about a fine-tuning job"""
        if jobid is None:jobid = self.jobid
        assert jobid is not None, "jobid must be specified"
        resp = retrievejob(self.api_key, self.base_url, jobid)
        self.modelid = resp["fine_tuned_model"]
        return resp
    
    def list_events(self, jobid:Union[str, None]=None, limit:int=0):
        """Get status updates for a fine-tuning job"""
        if jobid is None:jobid = self.jobid
        assert jobid is not None, "jobid must be specified"
        return listevents(self.api_key, self.base_url, jobid, limit)
    
    def cancel_job(self, jobid:Union[str, None]=None):
        """Cancel a fine-tuning job"""
        if jobid is None:jobid = self.jobid
        assert jobid is not None, "jobid must be specified"
        return canceljob(self.api_key, self.base_url, jobid)
    
    def delete_model(self, modelid:Union[str, None]=None):
        """Delete a fine-tuning model"""
        if modelid is None:modelid = self.modelid
        assert modelid is not None, "modelid must be specified"
        return deletemodel(self.api_key, self.base_url, modelid)

    def list_models(self, gpt_only:bool=True):
        """Get the valid models

        Args:
            gpt_only (bool, optional): whether to only show the GPT models. Defaults to True.

        Returns:
            List[str]: valid models
        """
        return valid_models(self.api_key, self.base_url, gpt_only=gpt_only)
    
    def __repr__(self) -> str:
        return f"<FineTune Job>"
    
    def __str__(self) -> str:
        return self.__repr__()

    @property
    def api_key(self) -> str:
        return self._api_key
    @api_key.setter
    def api_key(self, value:str) -> None:
        self._api_key = value

    @property
    def base_url(self) -> str:
        return self._base_url
    @base_url.setter
    def base_url(self, value:str) -> None:
        self._base_url = value
    
    @property
    def model(self) -> str:
        return self._model
    @model.setter
    def model(self, value:str) -> None:
        self._model = value
    
    @property
    def modelid(self) -> str:
        return self._modelid
    @modelid.setter
    def modelid(self, value:str) -> None:
        self._modelid = value
    
    @property
    def jobid(self) -> str:
        return self._jobid
    @jobid.setter
    def jobid(self, value:str) -> None:
        self._jobid = value
    
    @property
    def trainingid(self) -> str:
        return self._trainingid
    @trainingid.setter
    def trainingid(self, value:str) -> None:
        self._trainingid = value
    
    @property
    def validationid(self) -> str:
        return self._validationid
    @validationid.setter
    def validationid(self, value:str) -> None:
        self._validationid = value