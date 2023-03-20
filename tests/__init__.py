"""Unit test package for openai_api_call."""

# import pdb
import responses
import requests

mock_resp = {
    "choices": [{
        "message": {
            "content": "Response from GPT-3"
        }
    }],
    "usage": {
        "total_tokens": 100
    }
}

@responses.activate
def test_simple():
    responses.add(responses.GET, 'https://api.openai.com/v1/chat/completions',
                  json=mock_resp, status=200)
    resp = requests.get('https://api.openai.com/v1/chat/completions')
    assert resp.json() == mock_resp
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == 'https://api.openai.com/v1/chat/completions'
    assert responses.calls[0].response.text == '{"choices": [{"message": {"content": "Response from GPT-3"}}], "usage": {"total_tokens": 100}}'