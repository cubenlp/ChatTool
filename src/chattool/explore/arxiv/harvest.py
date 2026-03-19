"""arXiv OAI-PMH harvester for bulk metadata collection."""
from datetime import date
from typing import Iterator, Optional
from xml.etree import ElementTree as ET

import requests

from .models import Paper

_OAI_URL = "https://export.arxiv.org/oai2"
_NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "arxiv": "http://arxiv.org/OAI/arXiv/",
}


def _parse_record(record_el) -> Optional[Paper]:
    metadata = record_el.find("oai:metadata", _NS)
    if metadata is None:
        return None
    arx = metadata.find("arxiv:arXiv", _NS)
    if arx is None:
        return None

    def text(tag):
        el = arx.find(f"arxiv:{tag}", _NS)
        return el.text.strip() if el is not None and el.text else None

    arxiv_id = text("id")
    title = text("title") or ""
    abstract = text("abstract") or ""
    authors = [
        " ".join(filter(None, [
            a.findtext("arxiv:forenames", namespaces=_NS),
            a.findtext("arxiv:keyname", namespaces=_NS),
        ]))
        for a in arx.findall("arxiv:authors/arxiv:author", _NS)
    ]
    categories_str = text("categories") or ""
    categories = categories_str.split()

    from datetime import datetime, timezone
    created = text("created")
    updated = text("updated") or created
    published = datetime.fromisoformat(created).replace(tzinfo=timezone.utc) if created else datetime.now(timezone.utc)
    updated_dt = datetime.fromisoformat(updated).replace(tzinfo=timezone.utc) if updated else published

    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        summary=abstract,
        authors=authors,
        categories=categories,
        published=published,
        updated=updated_dt,
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
        doi=text("doi"),
        comment=text("comments"),
        journal_ref=text("journal-ref"),
    )


class ArxivHarvester:
    """Bulk metadata harvester using the arXiv OAI-PMH interface."""

    def __init__(self, delay: float = 5.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "chattool-arxiv-harvester/1.0"

    def _get(self, params: dict) -> ET.Element:
        import time
        resp = self.session.get(_OAI_URL, params=params, timeout=30)
        resp.raise_for_status()
        time.sleep(self.delay)
        return ET.fromstring(resp.content)

    def harvest(
        self,
        category: str,
        from_date: Optional[date] = None,
        until_date: Optional[date] = None,
    ) -> Iterator[Paper]:
        """Yield Papers from OAI-PMH ListRecords, optionally filtered by date range."""
        params = {"verb": "ListRecords", "metadataPrefix": "arXiv", "set": category}
        if from_date:
            params["from"] = from_date.isoformat()
        if until_date:
            params["until"] = until_date.isoformat()

        while True:
            root = self._get(params)
            list_records = root.find("oai:ListRecords", _NS)
            if list_records is None:
                break
            for record in list_records.findall("oai:record", _NS):
                paper = _parse_record(record)
                if paper:
                    yield paper

            token_el = list_records.find("oai:resumptionToken", _NS)
            if token_el is None or not token_el.text:
                break
            params = {"verb": "ListRecords", "resumptionToken": token_el.text.strip()}

    def harvest_since(self, category: str, from_date: date) -> Iterator[Paper]:
        return self.harvest(category, from_date=from_date)
