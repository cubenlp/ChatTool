import base64
import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9pX6lz8AAAAASUVORK5CYII="
)


def test_chattool_lark_send_file_task(lark_testkit):
    if not lark_testkit.default_receiver_id:
        pytest.skip("FEISHU_DEFAULT_RECEIVER_ID is required for file send coverage")

    file_path = lark_testkit.tmp_path / "send-file.txt"
    file_path.write_text("chattool send file task\n", encoding="utf-8")
    file_result = lark_testkit.invoke("lark", "send", "--file", str(file_path))
    file_message_id = lark_testkit.message_id_from_output(file_result.output)
    assert file_message_id

    file_message = lark_testkit.bot.get_message(file_message_id)
    assert file_message.success(), f"get_message failed: {file_message.code} {file_message.msg}"
    file_body = json.loads(file_message.data.items[0].body.content)
    assert "file_key" in file_body

    image_path = lark_testkit.tmp_path / "send-image.png"
    image_path.write_bytes(PNG_1X1)
    image_result = lark_testkit.invoke("lark", "send", "--image", str(image_path))
    image_message_id = lark_testkit.message_id_from_output(image_result.output)
    assert image_message_id

    image_message = lark_testkit.bot.get_message(image_message_id)
    assert image_message.success(), f"get_message failed: {image_message.code} {image_message.msg}"
    image_body = json.loads(image_message.data.items[0].body.content)
    assert "image_key" in image_body

