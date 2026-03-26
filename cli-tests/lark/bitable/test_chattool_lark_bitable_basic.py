import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_bitable_basic(lark_testkit):
    app_name = lark_testkit.unique_name("cli-bitable")
    app_result = lark_testkit.invoke("lark", "bitable", "app", "create", app_name)
    app_payload = lark_testkit.parse_json(app_result.output)
    app_token = lark_testkit.find_value(app_payload, "app_token")
    assert app_token

    table_list = lark_testkit.invoke("lark", "bitable", "table", "list", app_token)
    assert "tables" in table_list.output or "items" in table_list.output

    table_name = lark_testkit.unique_name("records")
    table_create = lark_testkit.invoke("lark", "bitable", "table", "create", app_token, table_name)
    table_payload = lark_testkit.parse_json(table_create.output)
    table_id = lark_testkit.find_value(table_payload, "table_id")
    assert table_id

    field_list = lark_testkit.invoke("lark", "bitable", "field", "list", app_token, table_id)
    field_payload = lark_testkit.parse_json(field_list.output)
    items = lark_testkit.find_value(field_payload, "items") or []
    assert items
    primary_field_name = items[0]["field_name"]

    record_path = lark_testkit.tmp_path / "record.json"
    record_path.write_text(
        json.dumps({primary_field_name: lark_testkit.unique_name("row")}, ensure_ascii=False),
        encoding="utf-8",
    )
    record_create = lark_testkit.invoke(
        "lark",
        "bitable",
        "record",
        "create",
        app_token,
        table_id,
        "--json",
        str(record_path),
    )
    record_payload = lark_testkit.parse_json(record_create.output)
    assert lark_testkit.find_value(record_payload, "record_id")

    records_path = lark_testkit.tmp_path / "records.json"
    records_path.write_text(
        json.dumps(
            [
                {primary_field_name: lark_testkit.unique_name("batch-a")},
                {primary_field_name: lark_testkit.unique_name("batch-b")},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    batch_create = lark_testkit.invoke(
        "lark",
        "bitable",
        "record",
        "batch-create",
        app_token,
        table_id,
        "--json",
        str(records_path),
    )
    assert "记录批量创建成功" in batch_create.output
