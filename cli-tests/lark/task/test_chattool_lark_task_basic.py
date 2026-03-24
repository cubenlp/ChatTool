from datetime import datetime, timedelta, timezone

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_task_basic(lark_testkit):
    create_args = [
        "lark",
        "task",
        "create",
        "--summary",
        lark_testkit.unique_name("cli-task"),
        "--due",
        (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
    ]
    if lark_testkit.test_user_id:
        create_args.append("--add-test-user")
    create = lark_testkit.invoke(*create_args)
    create_payload = lark_testkit.parse_json(create.output)
    task_guid = lark_testkit.find_value(create_payload, "guid") or lark_testkit.find_value(create_payload, "task_guid")
    assert task_guid

    get_result = lark_testkit.invoke("lark", "task", "get", task_guid)
    assert task_guid in get_result.output

    patch_result = lark_testkit.invoke(
        "lark",
        "task",
        "patch",
        task_guid,
        "--completed-at",
        datetime.now(timezone.utc).isoformat(),
    )
    assert "任务更新成功" in patch_result.output

    tasklist_create = lark_testkit.invoke(
        "lark",
        "task",
        "tasklist",
        "create",
        lark_testkit.unique_name("cli-tasklist"),
    )
    tasklist_payload = lark_testkit.parse_json(tasklist_create.output)
    tasklist_guid = lark_testkit.find_value(tasklist_payload, "guid") or lark_testkit.find_value(tasklist_payload, "tasklist_guid")
    assert tasklist_guid

    tasklist_list = lark_testkit.invoke("lark", "task", "tasklist", "list")
    assert "任务清单列表获取成功" in tasklist_list.output

    tasks_result = lark_testkit.invoke("lark", "task", "tasklist", "tasks", tasklist_guid)
    assert "清单任务列表获取成功" in tasks_result.output

    if lark_testkit.test_user_id:
        add_members = lark_testkit.invoke(
            "lark",
            "task",
            "tasklist",
            "add-members",
            tasklist_guid,
            "--add-test-user",
        )
        assert "任务清单成员添加成功" in add_members.output
