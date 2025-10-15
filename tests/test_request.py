from chattool import debug_log, Resp
from chattool.request import normalize_url, is_valid_url, valid_models
import pytest, chattool, os
api_key, base_url, api_base = chattool.api_key, chattool.base_url, chattool.api_base

def test_valid_models():
    if chattool.api_base:
        model_url = os.path.join(chattool.api_base, 'models')
    else:
        model_url = os.path.join(chattool.base_url, 'v1/models')
    models = valid_models(api_key, model_url, gpt_only=False)
    assert len(models) >= 1
    models = valid_models(api_key, model_url, gpt_only=True)
    assert len(models) >= 1
    assert 'gpt-3.5-turbo' in models

def test_debug_log():
    """Test the debug log"""
    assert debug_log(net_url="https://www.baidu.com") or debug_log(net_url="https://www.google.com")
    assert not debug_log(net_url="https://baidu123.com") # invalid url

# normalize base url
def test_is_valid_url():
    assert is_valid_url("http://api.openai.com") == True
    assert is_valid_url("https://www.google.com/") == True
    assert is_valid_url("ftp://ftp.debian.org/debian/") == True
    assert is_valid_url("api.openai.com") == False
    assert is_valid_url("example.com") == False

def test_normalize_url():
    assert normalize_url("http://api.openai.com") == "http://api.openai.com"
    assert normalize_url("https://www.google.com") == "https://www.google.com"
    assert normalize_url("ftp://ftp.debian.org/debian/dists/stable/main/installer-amd64/current/images/cdrom/boot.img.gz") == "ftp://ftp.debian.org/debian/dists/stable/main/installer-amd64/current/images/cdrom/boot.img.gz"
    assert normalize_url("api.openai.com") == "https://api.openai.com"
    assert normalize_url("example.com/foo/bar") == "https://example.com/foo/bar"
