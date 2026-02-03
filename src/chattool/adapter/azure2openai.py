from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from chattool.core.chattype import AzureChat
from chattool.adapter.utils import (
    ChatCompletionRequest, stream_generator, get_bearer_token, logger
)

app = FastAPI(title="Azure to OpenAI Proxy")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, raw_request: Request):
    try:
        # Convert messages to list of dicts
        messages_dict = [msg.dict(exclude_none=True) for msg in request.messages]
        
        # Get API Key from request header (Authorization: Bearer <key>)
        api_key = get_bearer_token(raw_request)
        
        chat = AzureChat(
            messages=messages_dict,
            model=request.model, # Forward model as is
            api_key=api_key,     # Forward API key from request header
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
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
