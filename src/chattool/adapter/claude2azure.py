from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import json
from chattool.core.chattype import ClaudeChat
from chattool.adapter.utils import logger

app = FastAPI(title="Claude to Azure Proxy")

class Message(BaseModel):
    role: str
    content: Optional[str] = None

class AzureChatRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None

async def azure_stream_generator(chat: ClaudeChat):
    """Generate Azure/OpenAI-style SSE events from ClaudeChat stream"""
    try:
        # ClaudeChat.async_get_response_stream returns ChatResponse objects which are already converted to OpenAI format!
        # Looking at chattype.py: ClaudeChat.async_chat_completion calls _convert_response.
        # However, async_get_response_stream uses chat_completion_stream_async.
        # Let's check if ClaudeChat.chat_completion_stream_async also converts.
        
        async for response in chat.async_get_response_stream(update_history=False):
            # response.response is already in OpenAI/Azure format thanks to ClaudeChat implementation
            chunk_data = response.response
            yield f"data: {json.dumps(chunk_data)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Stream error: {e}")
        error_data = {"error": {"message": str(e), "type": "internal_error"}}
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/openai/deployments/{deployment_id}/chat/completions")
async def chat_completions(
    deployment_id: str, 
    request: AzureChatRequest, 
    raw_request: Request,
    api_version: Optional[str] = None
):
    try:
        messages_dict = [msg.dict(exclude_none=True) for msg in request.messages]
        
        # Azure uses api-key header
        api_key = raw_request.headers.get("api-key")
        
        chat = ClaudeChat(
            messages=messages_dict,
            model=deployment_id, # Use deployment_id as model name
            api_key=api_key,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
        )
        
        if request.stream:
            return StreamingResponse(
                azure_stream_generator(chat), 
                media_type="text/event-stream"
            )
        else:
            response = await chat.async_get_response(update_history=False)
            # ClaudeChat.async_get_response already returns OpenAI format
            return JSONResponse(content=response.response)
            
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
