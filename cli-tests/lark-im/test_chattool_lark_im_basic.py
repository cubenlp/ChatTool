import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_im_basic(lark_testkit):
    if not lark_testkit.message_receiver_id:
        pytest.skip("No Feishu receiver configured for IM tests")

    text = lark_testkit.unique_name("cli-im")
    send_resp = lark_testkit.bot.send_text(
        lark_testkit.message_receiver_id,
        lark_testkit.message_receiver_type,
        text,
    )
    assert send_resp.success(), f"send_text failed: {send_resp.code} {send_resp.msg}"
    message_id = send_resp.data.message_id

    get_resp = lark_testkit.bot.get_message(message_id)
    assert get_resp.success(), f"get_message failed: {get_resp.code} {get_resp.msg}"
    chat_id = get_resp.data.items[0].chat_id

    list_result = lark_testkit.invoke(
        "lark",
        "im",
        "list",
        "--chat-id",
        chat_id,
        "--relative-hours",
        "1",
    )
    assert message_id in list_result.output or text in list_result.output

    upload_path = lark_testkit.tmp_path / "download-source.txt"
    upload_content = b"chattool lark im download\n"
    upload_path.write_bytes(upload_content)

    upload_resp = lark_testkit.bot.upload_file(str(upload_path))
    assert upload_resp.success(), f"upload_file failed: {upload_resp.code} {upload_resp.msg}"
    file_key = upload_resp.data.file_key

    file_send_resp = lark_testkit.bot._send_message(  # noqa: SLF001
        lark_testkit.message_receiver_id,
        lark_testkit.message_receiver_type,
        "file",
        json.dumps({"file_key": file_key}),
    )
    assert file_send_resp.success(), f"send file failed: {file_send_resp.code} {file_send_resp.msg}"

    file_message_resp = lark_testkit.bot.get_message(file_send_resp.data.message_id)
    assert file_message_resp.success(), f"get file message failed: {file_message_resp.code} {file_message_resp.msg}"
    message_file_key = json.loads(file_message_resp.data.items[0].body.content)["file_key"]

    output_path = lark_testkit.tmp_path / "downloaded.txt"
    download_result = lark_testkit.invoke(
        "lark",
        "im",
        "download",
        file_send_resp.data.message_id,
        message_file_key,
        "--type",
        "file",
        "--output",
        str(output_path),
    )
    assert "资源下载成功" in download_result.output
    assert output_path.read_bytes() == upload_content
