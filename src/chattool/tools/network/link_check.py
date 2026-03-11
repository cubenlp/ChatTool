import re
import ssl
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


URL_RE = re.compile(r"https?://[^\s)>\"]+")


@dataclass(frozen=True)
class LinkCheckResult:
    url: str
    ok: bool
    status: Optional[int]
    elapsed_ms: int
    error: Optional[str]


@dataclass(frozen=True)
class ServiceCheckResult:
    url: str
    expected: str
    ok: bool
    status: Optional[int]
    elapsed_ms: int
    matched: bool
    error: Optional[str]


def extract_urls(text: str) -> List[str]:
    return URL_RE.findall(text)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def collect_urls(path: Path, globs: Sequence[str]) -> List[str]:
    urls: List[str] = []
    if path.is_file():
        urls.extend(extract_urls(_read_text(path)))
        return urls

    for pattern in globs:
        for file_path in path.rglob(pattern):
            if file_path.is_file():
                urls.extend(extract_urls(_read_text(file_path)))
    return urls


def _request(url: str, timeout: float, method: str) -> int:
    req = Request(
        url,
        method=method,
        headers={
            "User-Agent": "chattool-link-check/1.0",
            "Accept": "*/*",
        },
    )
    context = ssl.create_default_context()
    with urlopen(req, timeout=timeout, context=context) as resp:
        return resp.status


def check_url(url: str, timeout: float) -> LinkCheckResult:
    start = time.monotonic()
    try:
        status = _request(url, timeout, "HEAD")
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return LinkCheckResult(url=url, ok=200 <= status < 400, status=status, elapsed_ms=elapsed_ms, error=None)
    except HTTPError as exc:
        if exc.code in {400, 403, 405}:
            try:
                status = _request(url, timeout, "GET")
                elapsed_ms = int((time.monotonic() - start) * 1000)
                return LinkCheckResult(url=url, ok=200 <= status < 400, status=status, elapsed_ms=elapsed_ms, error=None)
            except Exception as retry_exc:  # noqa: BLE001 - user-facing error context
                elapsed_ms = int((time.monotonic() - start) * 1000)
                return LinkCheckResult(
                    url=url,
                    ok=False,
                    status=None,
                    elapsed_ms=elapsed_ms,
                    error=str(retry_exc),
                )

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return LinkCheckResult(url=url, ok=False, status=exc.code, elapsed_ms=elapsed_ms, error=str(exc))
    except (URLError, OSError, TimeoutError) as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return LinkCheckResult(url=url, ok=False, status=None, elapsed_ms=elapsed_ms, error=str(exc))


def check_urls(urls: Iterable[str], timeout: float) -> List[LinkCheckResult]:
    seen: Set[str] = set()
    results: List[LinkCheckResult] = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        results.append(check_url(url, timeout))
    return results


def _request_text(url: str, timeout: float, max_bytes: int) -> tuple[int, str]:
    req = Request(
        url,
        method="GET",
        headers={
            "User-Agent": "chattool-link-check/1.0",
            "Accept": "*/*",
        },
    )
    context = ssl.create_default_context()
    with urlopen(req, timeout=timeout, context=context) as resp:
        data = resp.read(max_bytes)
        text = data.decode("utf-8", errors="ignore")
        return resp.status, text


def check_service_url(url: str, expected: str, timeout: float, max_bytes: int = 65536) -> ServiceCheckResult:
    start = time.monotonic()
    expected_lower = expected.lower()
    try:
        status, text = _request_text(url, timeout, max_bytes)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        content_lower = text.lower()
        matched = expected_lower in content_lower or expected_lower in url.lower()
        ok = 200 <= status < 400 and matched
        error = None if ok else f"missing expected token: {expected}"
        return ServiceCheckResult(
            url=url,
            expected=expected,
            ok=ok,
            status=status,
            elapsed_ms=elapsed_ms,
            matched=matched,
            error=error,
        )
    except HTTPError as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ServiceCheckResult(
            url=url,
            expected=expected,
            ok=False,
            status=exc.code,
            elapsed_ms=elapsed_ms,
            matched=False,
            error=str(exc),
        )
    except (URLError, OSError, TimeoutError) as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ServiceCheckResult(
            url=url,
            expected=expected,
            ok=False,
            status=None,
            elapsed_ms=elapsed_ms,
            matched=False,
            error=str(exc),
        )
