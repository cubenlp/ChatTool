import chattool.cli.client.network as network_module


def test_append_token_adds_when_missing():
    url = "http://example.com/json/version"
    out = network_module._append_token(url, "abc")
    assert "token=abc" in out
    assert out.startswith("http://example.com/json/version?")


def test_append_token_keeps_existing():
    url = "http://example.com/json/version?token=abc"
    out = network_module._append_token(url, "zzz")
    assert out == url


def test_append_token_preserves_query():
    url = "http://example.com/json/version?foo=bar"
    out = network_module._append_token(url, "abc")
    assert "foo=bar" in out
    assert "token=abc" in out
