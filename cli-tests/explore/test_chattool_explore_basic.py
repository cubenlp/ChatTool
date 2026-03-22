from datetime import datetime

import pytest
from click.testing import CliRunner

from chattool.client.main import cli
from chattool.explore.arxiv.models import Paper


pytestmark = pytest.mark.e2e


def _paper(
    arxiv_id: str,
    title: str,
    summary: str,
    categories: list[str] | None = None,
) -> Paper:
    now = datetime(2024, 1, 1)
    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        summary=summary,
        authors=["Alice", "Bob"],
        categories=categories or ["cs.AI"],
        published=now,
        updated=now,
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
    )


@pytest.fixture
def runner():
    return CliRunner()


def test_explore_help_commands(runner):
    result = runner.invoke(cli, ["explore", "--help"])
    assert result.exit_code == 0
    assert "arxiv" in result.output

    result = runner.invoke(cli, ["explore", "arxiv", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output
    assert "daily" in result.output
    assert "get" in result.output
    assert "presets" in result.output

    result = runner.invoke(cli, ["explore", "arxiv", "search", "--help"])
    assert result.exit_code == 0
    assert "--preset" in result.output
    assert "--category" in result.output
    assert "--keyword" in result.output


def test_explore_arxiv_search_uses_preset_query(monkeypatch, runner):
    import chattool.explore.arxiv as arxiv_mod

    calls = {}

    class FakeArxivClient:
        def search(self, query, max_results=10, sort_by="submittedDate"):
            calls["query"] = query
            calls["max_results"] = max_results
            calls["sort_by"] = sort_by
            return [
                _paper(
                    "2401.00001",
                    "Autoformalization with Lean 4",
                    "A paper about theorem proving and autoformalization.",
                )
            ]

        def filter_papers(self, papers, categories=None, keywords=None):
            return papers

    def fake_build_query(categories=None, keywords=None, title=None, abstract=None, author=None):
        calls["build_categories"] = categories
        calls["build_keywords"] = keywords
        return "preset-query"

    monkeypatch.setattr(arxiv_mod, "ArxivClient", FakeArxivClient)
    monkeypatch.setattr(arxiv_mod, "build_query", fake_build_query)

    result = runner.invoke(cli, ["explore", "arxiv", "search", "-p", "ai4math", "-n", "2"])
    assert result.exit_code == 0
    assert calls["query"] == "preset-query"
    assert calls["max_results"] == 2
    assert calls["sort_by"] == "submittedDate"
    assert "Found 1 paper(s)" in result.output
    assert "Autoformalization with Lean 4" in result.output


def test_explore_arxiv_daily_applies_preset_filter(monkeypatch, runner):
    import chattool.explore.arxiv as arxiv_mod

    class FakeDailyFetcher:
        def since(self, days=1, categories=None, keywords=None, max_results=200):
            return [
                _paper(
                    "2401.00002",
                    "Lean 4 autoformalization for theorem proving",
                    "Autoformalization for interactive theorem proving.",
                ),
                _paper(
                    "2401.00003",
                    "Vision transformers for image generation",
                    "An unrelated paper in the same category.",
                ),
            ]

    monkeypatch.setattr(arxiv_mod, "DailyFetcher", FakeDailyFetcher)

    result = runner.invoke(
        cli,
        ["explore", "arxiv", "daily", "-p", "math-formalization", "--days", "3"],
    )
    assert result.exit_code == 0
    assert "1 paper(s) from last 3 days" in result.output
    assert "Lean 4 autoformalization for theorem proving" in result.output
    assert "Vision transformers for image generation" not in result.output


def test_explore_arxiv_get_verbose(monkeypatch, runner):
    import chattool.explore.arxiv as arxiv_mod

    class FakeArxivClient:
        def get_by_id(self, arxiv_id):
            assert arxiv_id == "1706.03762"
            return _paper(
                "1706.03762",
                "Attention Is All You Need",
                "The Transformer architecture removes recurrence entirely.",
                categories=["cs.CL"],
            )

    monkeypatch.setattr(arxiv_mod, "ArxivClient", FakeArxivClient)

    result = runner.invoke(cli, ["explore", "arxiv", "get", "1706.03762", "-v"])
    assert result.exit_code == 0
    assert "Attention Is All You Need" in result.output
    assert "Abstract:" in result.output
    assert "removes recurrence entirely" in result.output


def test_explore_arxiv_presets_lists_known_entries(runner):
    result = runner.invoke(cli, ["explore", "arxiv", "presets"])
    assert result.exit_code == 0
    assert "ai4math" in result.output
    assert "math-formalization" in result.output
    assert "math-formalization-weekly" in result.output
