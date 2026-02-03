from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import json
from chattool.core.chattype import Chat
from chattool.utils import setup_logger

logger = setup_logger("ProxyAdapter")

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

async def stream_generator(chat: Chat):
    """Generate SSE events from Chat stream"""
    try:
        async for response in chat.async_get_response_stream(update_history=False):
            # response.response is the chunk dict
            chunk_data = response.response
            yield f"data: {json.dumps(chunk_data)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Stream error: {e}")
        error_data = {"error": {"message": str(e), "type": "internal_error"}}
        yield f"data: {json.dumps(error_data)}\n\n"

def get_bearer_token(request: Request) -> Optional[str]:
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    return None
