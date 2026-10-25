"""Shared OpenAI schema plus ChatTool's independent API connectivity probes."""

from dataclasses import dataclass
import json
import time

from chatenv.configs import OpenAIConfig


@dataclass(frozen=True)
class OpenAIProbeResult:
    """Secret-safe outcome of one protocol's minimal text generation probe."""

    protocol: str
    success: bool
    detail: str


def _parse_responses_stream_event(cls, line: str):
    if not line.startswith("data:"):
        return None
    payload = line.removeprefix("data:").strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        event = json.loads(payload)
        return event if isinstance(event, dict) else None
    except json.JSONDecodeError:
        return None


def _validate_responses_stream(cls, response, *, deadline=None) -> str:
    generated = False
    for line in response.iter_lines():
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError
        event = cls._parse_responses_stream_event(line)
        if not event:
            continue
        event_type = event.get("type")
        if event_type in ("response.failed", "error", "response.cancelled"):
            # Never echo server-controlled error text or response content.
            raise ValueError(event_type)
        if event_type == "response.incomplete":
            details = (event.get("response") or {}).get("incomplete_details") or {}
            if details.get("reason") == "max_output_tokens":
                raise ValueError("response.incomplete: test token budget exhausted")
            raise ValueError("response.incomplete")
        if event_type == "response.output_text.delta" and event.get("delta"):
            generated = True
        if event_type == "response.completed":
            # Some compatible endpoints include text only in the final event.
            output = (event.get("response") or {}).get("output") or []
            generated = generated or any(
                isinstance(item, dict)
                and any(
                    isinstance(content, dict)
                    and content.get("type") == "output_text"
                    and bool(content.get("text"))
                    for content in (item.get("content") or [])
                )
                for item in output
            )
            if generated:
                return "generated and completed"
            raise ValueError("completed without text output")
    raise ValueError("Responses stream ended before text output and completion")


def _probe_responses(*, api_base, api_key, model, timeout):
    import httpx

    deadline = time.monotonic() + timeout
    with httpx.Client(timeout=timeout) as client:
        with client.stream(
            "POST", f"{api_base.rstrip('/')}/responses",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "input": [{"role": "user", "content": "Reply with OK only."}],
                "max_output_tokens": 256,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            return OpenAIConfig._validate_responses_stream(response, deadline=deadline)


def _probe_chat_completions(*, api_base, api_key, model, timeout):
    import httpx

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{api_base.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with OK only."}],
                "max_completion_tokens": 256,
            },
        )
        response.raise_for_status()
        data = response.json()
    if not isinstance(data, dict) or data.get("error"):
        raise ValueError("invalid Chat Completions response")
    choices = data.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        raise ValueError("no completion choices")
    choice = choices[0]
    if choice.get("finish_reason") == "length":
        raise ValueError("test token budget exhausted")
    if choice.get("finish_reason") != "stop":
        raise ValueError("completion did not finish normally")
    content = (choice.get("message") or {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("completed without text output")
    return "generated and completed"


def probe_openai_apis(*, api_base, api_key, model, timeout=30.0):
    """Probe Responses first, then Chat Completions, without changing profiles.

    Return both outcomes even if the first protocol fails. Each probe has a
    30-second HTTP timeout and no automatic retry. Results never include keys,
    URLs, server error bodies or generated content. A token-budget failure is
    a failed smoke test, not evidence that the protocol is unsupported.
    """
    import httpx

    probes = (("Responses API", _probe_responses), ("Chat Completions API", _probe_chat_completions))
    missing = [name for name, value in (
        ("OPENAI_API_BASE", api_base), ("OPENAI_API_KEY", api_key), ("OPENAI_API_MODEL", model)
    ) if not value]
    if missing:
        return tuple(OpenAIProbeResult(name, False, "Not set: " + ", ".join(missing)) for name, _ in probes)
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    results = []
    for name, probe in probes:
        try:
            detail = probe(api_base=api_base, api_key=api_key, model=model, timeout=timeout)
            results.append(OpenAIProbeResult(name, True, detail))
        except httpx.HTTPStatusError as exc:
            results.append(OpenAIProbeResult(name, False, f"HTTP {exc.response.status_code}"))
        except (httpx.TimeoutException, TimeoutError):
            results.append(OpenAIProbeResult(name, False, "Request timeout"))
        except httpx.RequestError:
            results.append(OpenAIProbeResult(name, False, "Connection/request error"))
        except ValueError as exc:
            # Only expose diagnostics generated here, never response.json()
            # parsing errors or arbitrary third-party exception messages.
            safe_details = {
                "response.failed", "error", "response.cancelled", "response.incomplete",
                "response.incomplete: test token budget exhausted",
                "completed without text output", "Responses stream ended before text output and completion",
                "invalid Chat Completions response", "no completion choices",
                "test token budget exhausted", "completion did not finish normally",
            }
            detail = str(exc) if str(exc) in safe_details else "Invalid API response"
            results.append(OpenAIProbeResult(name, False, detail))
        except Exception:
            results.append(OpenAIProbeResult(name, False, "Invalid API response"))
    return tuple(results)


def _test_responses_api(cls):
    """Compatibility hook for callers of the former Responses-only helper."""
    return _probe_responses(
        api_base=cls.OPENAI_API_BASE.value, api_key=cls.OPENAI_API_KEY.value,
        model=cls.OPENAI_API_MODEL.value, timeout=30.0,
    )


def _test(cls):
    import click

    print(f"Testing {cls._title}...")
    results = probe_openai_apis(
        api_base=cls.OPENAI_API_BASE.value, api_key=cls.OPENAI_API_KEY.value,
        model=cls.OPENAI_API_MODEL.value,
    )
    for result in results:
        print(f"{'✅' if result.success else '❌'} {result.protocol}: {result.detail}")
    if not any(result.success for result in results):
        raise click.ClickException("Neither API passed the generation test; see per-protocol results above.")
    if all(result.success for result in results):
        print("✅ Both APIs passed the generation test.")
    else:
        print("✅ Configuration is usable via the passing API; the other API did not pass this test.")
    return results


OpenAIConfig._parse_responses_stream_event = classmethod(_parse_responses_stream_event)
OpenAIConfig._validate_responses_stream = classmethod(_validate_responses_stream)
OpenAIConfig._test_responses_api = classmethod(_test_responses_api)
OpenAIConfig.test = classmethod(_test)

__all__ = ["OpenAIConfig", "OpenAIProbeResult", "probe_openai_apis"]
