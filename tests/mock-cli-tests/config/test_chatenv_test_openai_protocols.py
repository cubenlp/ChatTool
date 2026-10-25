import importlib
import json

import httpx
import pytest
from click.testing import CliRunner

from chatenv.cli import cli
from chatenv.configs import OpenAIConfig
from chatenv.store import EnvStore

# Importing ChatTool installs the OpenAI test provider on the shared schema.
import chattool.config.openai as provider


CANARY = "DUMMY_SECRET_OR_GENERATED_CONTENT_MUST_NOT_BE_PRINTED"


def sse(*events):
    return "".join("data: " + json.dumps(event) + "\n\n" for event in events)


def response_events():
    return sse(
        {"type": "response.created"},
        {"type": "response.output_text.delta", "delta": CANARY},
        {"type": "response.completed", "response": {"status": "completed"}},
    )


def chat_result():
    return {"choices": [{"message": {"role": "assistant", "content": CANARY}, "finish_reason": "stop"}]}


@pytest.fixture
def cli_probe(monkeypatch, tmp_path):
    cli_module = importlib.import_module("chatenv.cli")
    monkeypatch.setattr(cli_module, "load_config_providers", lambda: None)
    fields = OpenAIConfig.get_fields()
    for field in fields.values():
        monkeypatch.setattr(field, "value", field.value)
    store = EnvStore(tmp_path / "envs")
    store.save_active(OpenAIConfig, {
        "OPENAI_API_BASE": "https://example.invalid/v1/",
        "OPENAI_API_KEY": CANARY,
        "OPENAI_API_MODEL": "active-model",
    })
    real_client = httpx.Client

    def run(responses_ok=True, chat_ok=True, responses_body=None, chat_body=None):
        calls = []

        def handler(request):
            calls.append(request)
            assert request.headers["Authorization"] == "Bearer " + CANARY
            if request.url.path == "/v1/responses":
                if not responses_ok:
                    return httpx.Response(404, json={"error": {"message": CANARY}})
                return httpx.Response(200, text=responses_body if responses_body is not None else response_events(), headers={"Content-Type": "text/event-stream"})
            assert request.url.path == "/v1/chat/completions"
            if not chat_ok:
                return httpx.Response(401, json={"error": {"message": CANARY}})
            return httpx.Response(200, json=chat_body if chat_body is not None else chat_result())

        monkeypatch.setattr(httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
        result = CliRunner().invoke(cli, ["--home", str(tmp_path), "test", "-t", "oai", "-I"])
        return result, calls

    return run, store


@pytest.mark.parametrize("responses_ok,chat_ok", [(True, True), (True, False), (False, True), (False, False)])
def test_cli_independently_reports_both_protocols(cli_probe, responses_ok, chat_ok):
    run, _ = cli_probe
    result, calls = run(responses_ok, chat_ok)
    assert [request.url.path for request in calls] == ["/v1/responses", "/v1/chat/completions"]
    assert result.exit_code == (0 if responses_ok or chat_ok else 1), result.output
    assert ("✅ Responses API" if responses_ok else "❌ Responses API") in result.output
    assert ("✅ Chat Completions API" if chat_ok else "❌ Chat Completions API") in result.output
    assert CANARY not in result.output
    for request in calls:
        assert json.loads(request.content)["model"] == "active-model"


def test_payloads_use_reasoning_compatible_token_budgets(cli_probe):
    run, _ = cli_probe
    _, calls = run()
    responses, chat = [json.loads(request.content) for request in calls]
    assert responses["max_output_tokens"] >= 256
    assert responses["stream"] is True
    assert "max_tokens" not in chat
    assert chat["max_completion_tokens"] >= 256


@pytest.mark.parametrize("body", [
    sse({"type": "response.created"}),
    sse({"type": "error", "error": {"message": CANARY}}),
    sse({"type": "response.failed", "response": {"error": {"message": CANARY}}}),
    sse({"type": "response.incomplete", "response": {"incomplete_details": {"reason": "max_output_tokens"}}}),
    sse({"type": "response.output_text.delta", "delta": CANARY}, {"type": "response.failed"}),
    sse({"type": "response.completed", "response": {"status": "completed"}}),
])
def test_responses_stream_errors_are_not_success_or_secret_output(cli_probe, body):
    run, _ = cli_probe
    result, calls = run(responses_body=body)
    assert len(calls) == 2
    assert "❌ Responses API" in result.output
    assert "✅ Chat Completions API" in result.output
    assert result.exit_code == 0
    assert CANARY not in result.output


@pytest.mark.parametrize("body", [
    {"error": {"message": CANARY}},
    {"choices": []},
    {"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]},
    {"choices": [{"message": {"content": CANARY}, "finish_reason": "length"}]},
])
def test_chat_invalid_results_are_not_success_or_secret_output(cli_probe, body):
    run, _ = cli_probe
    result, _ = run(chat_body=body)
    assert "❌ Chat Completions API" in result.output
    assert "✅ Responses API" in result.output
    assert result.exit_code == 0
    assert CANARY not in result.output


def test_python_probe_returns_structured_results(cli_probe):
    run, _ = cli_probe
    run()
    results = provider.probe_openai_apis(api_base="https://example.invalid/v1", api_key=CANARY, model="active-model")
    assert [(item.protocol, item.success) for item in results] == [("Responses API", True), ("Chat Completions API", True)]
    assert CANARY not in repr(results)


def test_selected_profile_is_used_without_activating_it(cli_probe, tmp_path):
    run, store = cli_probe
    store.save_profile(OpenAIConfig, "selected", {
        "OPENAI_API_BASE": "https://example.invalid/v1",
        "OPENAI_API_KEY": CANARY,
        "OPENAI_API_MODEL": "selected-model",
    })
    _, calls = run()
    calls.clear()
    result = CliRunner().invoke(cli, ["--home", str(tmp_path), "test", "selected", "-t", "openai", "-I"])
    assert result.exit_code == 0, result.output
    assert len(calls) == 2
    assert all(json.loads(request.content)["model"] == "selected-model" for request in calls)
    assert store.load_active(OpenAIConfig)["OPENAI_API_MODEL"] == "active-model"


def test_missing_configuration_does_not_send_requests(cli_probe):
    run, store = cli_probe
    store.save_active(OpenAIConfig, {"OPENAI_API_BASE": "", "OPENAI_API_KEY": "", "OPENAI_API_MODEL": ""})
    result, calls = run()
    assert not calls
    assert result.exit_code == 1
    assert "OPENAI_API_BASE" in result.output


def test_timeouts_are_independent_and_do_not_leak_exception_text(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout(CANARY, request=request)

    real_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
    results = provider.probe_openai_apis(api_base="https://example.invalid/v1", api_key=CANARY, model="active-model", timeout=1)
    assert len(calls) == 2
    assert all(not item.success and "timeout" in item.detail.lower() for item in results)
    assert CANARY not in repr(results)
