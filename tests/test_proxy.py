from openai_api_call import proxy_off, proxy_on
import os

def test_proxy():
    proxy_off()
    assert os.environ.get('http_proxy') is None
    assert os.environ.get('https_proxy') is None
    proxy_on("192.168.0.1")
    assert os.environ.get('http_proxy') == "http://192.168.0.1:7890"
    assert os.environ.get('https_proxy') == "https://192.168.0.1:7890"
    proxy_off()
    assert os.environ.get('http_proxy') is None
    assert os.environ.get('https_proxy') is None