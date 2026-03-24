from datetime import datetime, timedelta, timezone

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_calendar_basic(lark_testkit):
    primary = lark_testkit.invoke("lark", "calendar", "primary")
    primary_payload = lark_testkit.parse_json(primary.output)
    calendar_id = lark_testkit.find_value(primary_payload, "calendar_id")
    assert calendar_id

    start_dt = datetime.now(timezone.utc) + timedelta(hours=1)
    end_dt = start_dt + timedelta(hours=1)

    create = lark_testkit.invoke(
        "lark",
        "calendar",
        "event",
        "create",
        "--summary",
        lark_testkit.unique_name("cli-calendar"),
        "--start",
        start_dt.isoformat(),
        "--end",
        end_dt.isoformat(),
    )
    create_payload = lark_testkit.parse_json(create.output)
    event_id = lark_testkit.find_value(create_payload, "event_id")
    assert event_id

    get_result = lark_testkit.invoke("lark", "calendar", "event", "get", event_id)
    assert event_id in get_result.output

    list_result = lark_testkit.invoke(
        "lark",
        "calendar",
        "event",
        "list",
        "--start",
        (start_dt - timedelta(minutes=10)).isoformat(),
        "--end",
        (end_dt + timedelta(minutes=10)).isoformat(),
    )
    assert event_id in list_result.output

    patch_result = lark_testkit.invoke(
        "lark",
        "calendar",
        "event",
        "patch",
        event_id,
        "--summary",
        lark_testkit.unique_name("cli-calendar-updated"),
    )
    assert "日程更新成功" in patch_result.output

    if lark_testkit.test_user_id:
        freebusy = lark_testkit.invoke(
            "lark",
            "calendar",
            "freebusy",
            "list",
            "--start",
            start_dt.isoformat(),
            "--end",
            end_dt.isoformat(),
        )
        assert "忙闲信息获取成功" in freebusy.output
