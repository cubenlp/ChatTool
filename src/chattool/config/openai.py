"""OpenAIConfig compatibility re-export.

The shared OpenAI field schema lives in :mod:`chatenv.configs`. ChatTool
re-exports that canonical class and attaches ChatTool-specific connectivity
helpers when ChatTool is imported.
"""

import json

from chatenv.configs import OpenAIConfig


def _parse_responses_stream_event(cls, line: str):
    if not line.startswith("data:"):
        return None
    payload = line.removeprefix("data:").strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _validate_responses_stream(cls, response) -> str:
    for line in response.iter_lines():
        event = cls._parse_responses_stream_event(line)
        if not event:
            continue
        event_type = event.get("type")
        if event_type in ("response.failed", "error"):
            error = event.get("error") or event.get("response", {}).get("error")
            raise RuntimeError(error or event_type)
        if event_type == "response.output_text.delta" and event.get("delta"):
            return "generated"
        if event_type == "response.completed":
            return "completed"
        if event_type in ("response.incomplete", "response.cancelled"):
            raise RuntimeError(event_type)
    raise RuntimeError("Responses stream ended before output or completion event")


def _test_responses_api(cls):
    import httpx

    api_base = (cls.OPENAI_API_BASE.value or "").rstrip("/")
    api_key = cls.OPENAI_API_KEY.value
    model = cls.OPENAI_API_MODEL.value
    if not api_base:
        raise ValueError("OPENAI_API_BASE not set")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    if not model:
        raise ValueError("OPENAI_API_MODEL not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "input": [{"role": "user", "content": "hi"}],
        "max_output_tokens": 8,
        "stream": True,
    }
    with httpx.Client(timeout=30) as client:
        with client.stream(
            "POST", f"{api_base}/responses", json=data, headers=headers
        ) as response:
            response.raise_for_status()
            return cls._validate_responses_stream(response)


def _test(cls):
    print(f"Testing {cls._title}...")
    try:
        # Prefer the Responses API: current CRS/Codex-style OpenAI endpoints
        # expose models such as gpt-5.x through /responses rather than
        # /chat/completions. Use streaming for proxies that require it,
        # consume enough events to prove generation works, and do not print
        # response chunks because they may include context.
        try:
            result = cls._test_responses_api()
            print(f"✅ Success! Responses API {result}.")
            return
        except Exception as responses_error:
            try:
                from chattool.llm.chattype import Chat

                chat = Chat(messages=[{"role": "user", "content": "hi"}])
                resp = chat.get_response(max_tokens=5)
                print(f"✅ Success! Chat Completions API: {resp.content}")
                return
            except Exception as chat_error:
                raise RuntimeError(
                    "Responses API failed and Chat Completions fallback failed: "
                    f"responses={responses_error}; chat={chat_error}"
                )
    except Exception as e:
        print(f"❌ Failed: {e}")


OpenAIConfig._parse_responses_stream_event = classmethod(_parse_responses_stream_event)
OpenAIConfig._validate_responses_stream = classmethod(_validate_responses_stream)
OpenAIConfig._test_responses_api = classmethod(_test_responses_api)
OpenAIConfig.test = classmethod(_test)

__all__ = ["OpenAIConfig"]
