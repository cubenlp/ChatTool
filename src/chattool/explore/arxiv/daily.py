"""arXiv daily paper fetcher — get latest submissions by date/category."""
from datetime import date, datetime, timedelta, timezone
from typing import Iterator, List, Optional

from .models import Paper
from .query import build_query


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def _yesterday_utc() -> date:
    return _today_utc() - timedelta(days=1)


class DailyFetcher:
    """
    Fetch the latest arXiv submissions for given categories/keywords.

    arXiv submissions are batched by day. New papers appear after the
    daily deadline (14:00 ET / 18:00 UTC on weekdays). Weekend submissions
    appear on Monday.

    Usage::

        fetcher = DailyFetcher()
        papers = fetcher.today(categories=["cs.AI", "cs.LG"])
        papers = fetcher.since(days=3, categories=["cs.CV"], keywords=["diffusion"])
    """

    def __init__(self, delay: float = 3.0):
        import arxiv
        self._arxiv = arxiv
        self.client = arxiv.Client(delay_seconds=delay, page_size=100)

    def _fetch(
        self,
        from_date: date,
        until_date: Optional[date] = None,
        categories: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        max_results: Optional[int] = 200,
    ) -> List[Paper]:
        from .client import _to_paper

        # Date range filter using submittedDate
        until = until_date or from_date
        date_filter = f"submittedDate:[{from_date.strftime('%Y%m%d')}0000 TO {until.strftime('%Y%m%d')}2359]"

        base = build_query(
            categories=categories,
            keywords=keywords,
            title=title,
            author=author,
        )
        query = f"({base}) AND {date_filter}" if base else date_filter

        search = self._arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=self._arxiv.SortCriterion.SubmittedDate,
            sort_order=self._arxiv.SortOrder.Descending,
        )
        return [_to_paper(r) for r in self.client.results(search)]

    def today(
        self,
        categories: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        max_results: int = 200,
    ) -> List[Paper]:
        """Fetch papers submitted today (UTC)."""
        return self._fetch(
            _today_utc(),
            categories=categories, keywords=keywords,
            title=title, author=author, max_results=max_results,
        )

    def yesterday(
        self,
        categories: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        max_results: int = 200,
    ) -> List[Paper]:
        """Fetch papers submitted yesterday (UTC)."""
        return self._fetch(
            _yesterday_utc(),
            categories=categories, keywords=keywords,
            title=title, author=author, max_results=max_results,
        )

    def since(
        self,
        days: int = 1,
        categories: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        max_results: int = 500,
    ) -> List[Paper]:
        """Fetch papers submitted in the last N days."""
        if days < 1:
            raise ValueError("days must be >= 1")
        from_date = _today_utc() - timedelta(days=days - 1)
        return self._fetch(
            from_date, until_date=_today_utc(),
            categories=categories, keywords=keywords,
            title=title, author=author, max_results=max_results,
        )

    def on_date(
        self,
        target_date: date,
        categories: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        max_results: int = 200,
    ) -> List[Paper]:
        """Fetch papers submitted on a specific date."""
        return self._fetch(
            target_date,
            categories=categories, keywords=keywords,
            max_results=max_results,
        )
