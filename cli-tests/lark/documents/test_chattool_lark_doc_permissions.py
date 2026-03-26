import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_doc_permissions(lark_testkit):
    document = lark_testkit.create_document(prefix="cli-doc-perm")

    public_get = lark_testkit.invoke("lark", "doc", "perm-public-get", document.document_id)
    assert "permission_public" in public_get.output
    assert "link_share_entity" in public_get.output

    public_set = lark_testkit.invoke(
        "lark",
        "doc",
        "perm-public-set",
        document.document_id,
        "--share-entity",
        "same_tenant",
        "--link-share-entity",
        "tenant_editable",
    )
    assert "更新成功" in public_set.output
    assert '"share_entity": "same_tenant"' in public_set.output
    assert '"link_share_entity": "tenant_editable"' in public_set.output

    member_id = lark_testkit.default_receiver_id or lark_testkit.test_user_id
    if not member_id:
        pytest.skip("No Feishu member is available for permission-member test")

    member_type_map = {
        "user_id": "userid",
        "open_id": "openid",
        "union_id": "unionid",
        "email": "email",
    }
    member_type = member_type_map.get(lark_testkit.message_receiver_type)
    if not member_type:
        pytest.skip(f"Unsupported receiver type for permission-member test: {lark_testkit.message_receiver_type}")

    member_add = lark_testkit.invoke(
        "lark",
        "doc",
        "perm-member-add",
        document.document_id,
        member_id,
        "--member-type",
        member_type,
        "--perm",
        "edit",
    )
    assert "添加成功" in member_add.output
    assert member_id in member_add.output

    member_list = lark_testkit.invoke("lark", "doc", "perm-member-list", document.document_id)
    assert "获取成功" in member_list.output
    assert "perm=edit" in member_list.output or "perm=full_access" in member_list.output
    payload = lark_testkit.parse_json(member_list.output)
    items = payload.get("data", {}).get("items", [])
    assert items
    assert any(item.get("perm") in {"edit", "full_access"} for item in items)
