from chattool import debug_log, Resp
from chattool.request import (
    normalize_url, is_valid_url, valid_models,
    loadfile, deletefile, filelist, filecontent,
    create_finetune_job, list_finetune_job, retrievejob,
    listevents, canceljob, deletemodel
)
import pytest, chattool
api_key, base_url = chattool.api_key, chattool.base_url
testpath = 'tests/testfiles/'

def test_valid_models():
    models = valid_models(api_key, base_url, gpt_only=False)
    assert len(models) >= 1
    models = valid_models(api_key, base_url, gpt_only=True)
    assert len(models) >= 1
    assert 'gpt-3.5-turbo' in models

def test_debug_log():
    """Test the debug log"""
    assert debug_log(net_url="https://www.baidu.com") or debug_log(net_url="https://www.google.com")
    assert not debug_log(net_url="https://baidu123.com") # invalid url
    chattool.api_key = None
    chattool.show_apikey()
    chattool.api_key = api_key

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

def test_broken_requests():
    """Test the broken requests"""
    with open(testpath + "test.txt", "w") as f:
        f.write("hello world")
    # invalid file uploading
    with pytest.raises(Exception): # the file should be JSONL format
        loadfile(api_key, base_url, "test.txt")
    # invalid apikey
    with pytest.raises(Exception):
        filelist("sk-123", base_url)
    with pytest.raises(Exception):
        list_finetune_job("sk-123", base_url)
    # no such file
    with pytest.raises(Exception):
        filecontent(api_key, base_url, "xxx")
    # retrieve job
    with pytest.raises(Exception):
        retrievejob(api_key, base_url, "xxx")
    # list events
    with pytest.raises(Exception):
        listevents(api_key, base_url, "xxx")