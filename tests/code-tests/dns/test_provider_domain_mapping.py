from types import SimpleNamespace


def test_aliyun_describe_domains_maps_record_count(monkeypatch):
    from chattool.tools.dns import aliyun

    class FakeRequest:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    fake_record = SimpleNamespace(
        domain_name="example.com",
        domain_id="domain-1",
        record_count=7,
        create_time="2026-05-07T00:00Z",
        remark=None,
        tags=SimpleNamespace(tag=[]),
    )
    fake_response = SimpleNamespace(
        body=SimpleNamespace(
            domains=SimpleNamespace(
                domain=[fake_record],
            ),
        ),
    )
    fake_client = SimpleNamespace(describe_domains=lambda _request: fake_response)

    monkeypatch.setattr(
        aliyun,
        "alidns_models",
        SimpleNamespace(DescribeDomainsRequest=FakeRequest),
    )

    client = aliyun.AliyunDNSClient.__new__(aliyun.AliyunDNSClient)
    client.client = fake_client

    domains = client.describe_domains()

    assert domains == [
        {
            "DomainName": "example.com",
            "DomainId": "domain-1",
            "Status": "ENABLE",
            "RecordCount": 7,
            "CreateTime": "2026-05-07T00:00Z",
            "Remark": None,
            "Tags": [],
        }
    ]
