import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_basic(lark_testkit):
    info = lark_testkit.invoke("lark", "info")
    assert "名称" in info.output
    assert "激活状态" in info.output

    scopes = lark_testkit.invoke("lark", "scopes", "-f", "im")
    assert "关键能力分类" in scopes.output
    assert "im" in scopes.output.lower()

    if not lark_testkit.message_receiver_id:
        pytest.skip("No Feishu receiver configured for send/reply coverage")

    text = lark_testkit.unique_name("cli-basic")
    send = lark_testkit.invoke("lark", "send", lark_testkit.message_receiver_id, text)
    message_id = lark_testkit.message_id_from_output(send.output)
    assert message_id

    reply = lark_testkit.invoke("lark", "reply", message_id, "收到")
    assert "回复成功" in reply.output

    upload_path = lark_testkit.tmp_path / "upload-basic.txt"
    upload_path.write_text("chattool lark basic upload\n", encoding="utf-8")
    upload = lark_testkit.invoke("lark", "upload", str(upload_path))
    assert "上传成功" in upload.output
    assert "file_key=" in upload.output

    get_resp = lark_testkit.bot.get_message(message_id)
    assert get_resp.success(), f"get_message failed: {get_resp.code} {get_resp.msg}"
    body = json.loads(get_resp.data.items[0].body.content)
    assert body["text"] == text
