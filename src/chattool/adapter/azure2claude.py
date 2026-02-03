from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import json
from chattool.core.chattype import AzureChat
from chattool.adapter.utils import get_bearer_token, logger

app = FastAPI(title="Azure to Claude Proxy")

class Message(BaseModel):
    role: str
    content: str

class ClaudeRequest(BaseModel):
    model: str
    messages: List[Message]
    system: Optional[str] = None
    max_tokens: Optional[int] = 4096
    metadata: Optional[Dict[str, Any]] = None
    stop_sequences: Optional[List[str]] = None
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = None
    top_k: Optional[int] = None

async def claude_stream_generator(chat: AzureChat):
    """Generate Claude-style SSE events from AzureChat stream"""
    try:
        # Claude stream format is different from OpenAI
        # But for simplicity, we can try to map it if needed.
        # However, the user might just want the raw chunks or a converted version.
        # Most "Claude interface" users expect Anthropic's event stream.
        
        # This is a bit complex to implement perfectly without a full mapper.
        # For now, let's provide a basic implementation.
        async for response in chat.async_get_response_stream(update_history=False):
            # Convert OpenAI chunk to Claude chunk
            # OpenAI: {"choices": [{"delta": {"content": "..."}}]}
            # Claude: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "..."}}
            content = response.delta_content
            if content:
                chunk = {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": content}
                }
                yield f"data: {json.dumps(chunk)}\n\n"
        
        yield f"data: {json.dumps({'type': 'message_stop'})}\n\n"
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': {'type': 'internal_server_error', 'message': str(e)}})}\n\n"

@app.post("/v1/messages")
async def messages(request: ClaudeRequest, raw_request: Request):
    try:
        # Convert Claude messages to OpenAI format for AzureChat
        openai_messages = []
        if request.system:
            openai_messages.append({"role": "system", "content": request.system})
        for msg in request.messages:
            openai_messages.append({"role": msg.role, "content": msg.content})
            
        api_key = get_bearer_token(raw_request)
        
        chat = AzureChat(
            messages=openai_messages,
            model=request.model,
            api_key=api_key,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
        )
        
        if request.stream:
            return StreamingResponse(
                claude_stream_generator(chat),
                media_type="text/event-stream"
            )
        else:
            response = await chat.async_get_response(update_history=False)
            # Convert OpenAI response to Claude response
            # OpenAI: {"choices": [{"message": {"content": "..."}}]}
            # Claude: {"id": "...", "type": "message", "role": "assistant", "content": [{"type": "text", "text": "..."}]}
            openai_resp = response.response
            content = response.content
            
            claude_resp = {
                "id": openai_resp.get("id", "msg_default"),
                "type": "message",
                "role": "assistant",
                "model": openai_resp.get("model", request.model),
                "content": [{"type": "text", "text": content}],
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": openai_resp.get("usage", {}).get("prompt_tokens", 0),
                    "output_tokens": openai_resp.get("usage", {}).get("completion_tokens", 0)
                }
            }
            return JSONResponse(content=claude_resp)
            
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
