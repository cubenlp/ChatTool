from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import json
import logging
from chattool.core.chattype import AzureChat
from chattool.utils import setup_logger

# Setup logger
logger = setup_logger("AzureProxy")

app = FastAPI(title="Azure OpenAI Proxy")

class Message(BaseModel):
    role: str
    content: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
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

async def stream_generator(chat: AzureChat):
    """Generate SSE events from AzureChat stream"""
    try:
        async for response in chat.async_get_response_stream(update_history=False):
            # response.response is the chunk dict
            chunk_data = response.response
            yield f"data: {json.dumps(chunk_data)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Stream error: {e}")
        # Try to yield error if possible
        error_data = {"error": {"message": str(e), "type": "internal_error"}}
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        # Convert messages to list of dicts
        messages_dict = [msg.dict(exclude_none=True) for msg in request.messages]
        
        # Initialize AzureChat
        chat = AzureChat(
            messages=messages_dict,
            model=request.model,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            # Pass other kwargs that might be supported by underlying HTTPClient/AzureChat
        )
        
        if request.stream:
            return StreamingResponse(
                stream_generator(chat), 
                media_type="text/event-stream"
            )
        else:
            response = await chat.async_get_response(update_history=False)
            return JSONResponse(content=response.response)
            
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
