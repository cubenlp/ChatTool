from datetime import date

import pytest

from chattool.explore.arxiv.daily import DailyFetcher


def test_since_uses_exact_day_window(monkeypatch):
    calls = {}

    def fake_today():
        return date(2026, 3, 21)

    def fake_fetch(
        self,
        from_date,
        until_date=None,
        categories=None,
        keywords=None,
        title=None,
        author=None,
        max_results=200,
    ):
        calls["from_date"] = from_date
        calls["until_date"] = until_date
        calls["categories"] = categories
        calls["keywords"] = keywords
        calls["max_results"] = max_results
        return []

    monkeypatch.setattr("chattool.explore.arxiv.daily._today_utc", fake_today)
    monkeypatch.setattr(DailyFetcher, "_fetch", fake_fetch)

    fetcher = object.__new__(DailyFetcher)
    result = DailyFetcher.since(
        fetcher,
        days=7,
        categories=["cs.LO"],
        keywords=["lean4"],
        max_results=50,
    )

    assert result == []
    assert calls["from_date"] == date(2026, 3, 15)
    assert calls["until_date"] == date(2026, 3, 21)
    assert calls["categories"] == ["cs.LO"]
    assert calls["keywords"] == ["lean4"]
    assert calls["max_results"] == 50


def test_since_rejects_non_positive_days():
    fetcher = object.__new__(DailyFetcher)

    with pytest.raises(ValueError, match="days must be >= 1"):
        DailyFetcher.since(fetcher, days=0)
