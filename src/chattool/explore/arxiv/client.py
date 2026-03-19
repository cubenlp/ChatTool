"""arXiv query client wrapping the `arxiv` library."""
from typing import Iterator, List, Optional
from .models import Paper


def _to_paper(result) -> Paper:
    arxiv_id = result.entry_id.split("/abs/")[-1].split("v")[0]
    return Paper(
        arxiv_id=arxiv_id,
        title=result.title,
        summary=result.summary,
        authors=[a.name for a in result.authors],
        categories=result.categories,
        published=result.published,
        updated=result.updated,
        pdf_url=result.pdf_url,
        doi=result.doi,
        comment=result.comment,
        journal_ref=result.journal_ref,
    )


class ArxivClient:
    """Search and fetch arXiv papers via the Query API."""

    def __init__(self, delay: float = 3.0, page_size: int = 100):
        import arxiv
        self._arxiv = arxiv
        self.client = arxiv.Client(delay_seconds=delay, page_size=page_size)

    def search_iter(
        self,
        query: str,
        max_results: Optional[int] = 10,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> Iterator[Paper]:
        """Lazy iterator over search results."""
        sort_map = {
            "relevance": self._arxiv.SortCriterion.Relevance,
            "lastUpdatedDate": self._arxiv.SortCriterion.LastUpdatedDate,
            "submittedDate": self._arxiv.SortCriterion.SubmittedDate,
        }
        order_map = {
            "descending": self._arxiv.SortOrder.Descending,
            "ascending": self._arxiv.SortOrder.Ascending,
        }
        search = self._arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_map.get(sort_by, self._arxiv.SortCriterion.SubmittedDate),
            sort_order=order_map.get(sort_order, self._arxiv.SortOrder.Descending),
        )
        for result in self.client.results(search):
            yield _to_paper(result)

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[Paper]:
        return list(self.search_iter(query, max_results=max_results, **kwargs))

    def get_by_id(self, arxiv_id: str) -> Paper:
        search = self._arxiv.Search(id_list=[arxiv_id])
        result = next(self.client.results(search))
        return _to_paper(result)

    def get_by_ids(self, arxiv_ids: List[str]) -> List[Paper]:
        search = self._arxiv.Search(id_list=arxiv_ids)
        return [_to_paper(r) for r in self.client.results(search)]
