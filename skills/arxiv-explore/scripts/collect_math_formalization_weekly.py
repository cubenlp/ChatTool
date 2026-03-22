#!/usr/bin/env python3
"""Collect recent arXiv papers for mathematical formalization research."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from chattool.explore.arxiv import ArxivClient, Paper


@dataclass(frozen=True)
class QueryGroup:
    name: str
    description: str
    query: str


QUERY_GROUPS = (
    QueryGroup(
        name="itp-core",
        description="Core interactive theorem proving / proof assistant sweep.",
        query='cat:cs.LO AND (all:"interactive theorem proving" OR all:"proof assistant" OR all:"theorem proving")',
    ),
    QueryGroup(
        name="lean-case-studies",
        description="Lean, Mathlib, and adjacent machine-checked math case studies.",
        query='(abs:lean OR abs:coq OR abs:isabelle OR abs:metamath OR abs:mathlib) AND (abs:proof OR abs:formal)',
    ),
    QueryGroup(
        name="autoformalization",
        description="LLM-driven informal-to-formal and auto-formalization workflows.",
        query='(cat:cs.AI OR cat:cs.CL OR cat:cs.LO) AND (all:autoformalization OR all:"auto-formalization" OR all:"informal-to-formal")',
    ),
    QueryGroup(
        name="atp-benchmarks",
        description="ATP evaluation, benchmark, and Mathlib generalization tracking.",
        query='(cat:cs.AI OR cat:cs.LG OR cat:cs.LO) AND (all:"automated theorem prover" OR all:mathlib OR all:miniF2F OR all:ProofNet)',
    ),
    QueryGroup(
        name="adjacent-verified",
        description="Adjacent machine-verified or proof-carrying work worth screening.",
        query='(all:"formally verified" OR all:"machine-verified" OR all:"proof-carrying") AND (all:lean OR all:"proof assistant" OR all:certificate)',
    ),
)

STRICT_KEYWORDS = (
    "autoformalization",
    "auto-formalization",
    "informal-to-formal",
    "theorem proving",
    "automated theorem prover",
    "proof assistant",
    "interactive theorem proving",
    "lean 4",
    "lean4",
    "mathlib",
    "coq",
    "isabelle",
    "metamath",
    "formalization of",
    "formalizing",
    "formalized",
    "machine-verified",
    "formally verified",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect recent arXiv papers for mathematical formalization research.",
    )
    parser.add_argument("--days", type=int, default=7, help="Only keep papers from the last N days.")
    parser.add_argument(
        "--per-query",
        type=int,
        default=20,
        help="Maximum number of arXiv results to request per query group.",
    )
    parser.add_argument(
        "--group",
        action="append",
        default=[],
        help="Run only the named group. Repeatable.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Apply a second strict keyword filter after fetching.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show abstract excerpts for each paper.",
    )
    parser.add_argument(
        "--list-groups",
        action="store_true",
        help="List available query groups and exit.",
    )
    return parser.parse_args()


def is_strict_match(paper: Paper) -> bool:
    haystack = f"{paper.title}\n{paper.summary}".lower()
    return any(keyword in haystack for keyword in STRICT_KEYWORDS)


def select_groups(names: list[str]) -> list[QueryGroup]:
    if not names:
        return list(QUERY_GROUPS)
    by_name = {group.name: group for group in QUERY_GROUPS}
    unknown = sorted(set(names) - set(by_name))
    if unknown:
        raise SystemExit(f"Unknown group(s): {', '.join(unknown)}")
    return [by_name[name] for name in names]


def format_excerpt(text: str, limit: int = 220) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def gather_recent_papers(
    groups: list[QueryGroup],
    days: int,
    per_query: int,
    strict: bool,
) -> tuple[list[Paper], dict[str, set[str]], str]:
    client = ArxivClient()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    papers_by_id: dict[str, Paper] = {}
    matched_groups: dict[str, set[str]] = {}

    for group in groups:
        papers = client.search(group.query, max_results=per_query, sort_by="submittedDate")
        for paper in papers:
            if paper.published < cutoff:
                continue
            if strict and not is_strict_match(paper):
                continue
            papers_by_id.setdefault(paper.arxiv_id, paper)
            matched_groups.setdefault(paper.arxiv_id, set()).add(group.name)

    ordered = sorted(
        papers_by_id.values(),
        key=lambda paper: (paper.published, paper.arxiv_id),
        reverse=True,
    )
    return ordered, matched_groups, cutoff.date().isoformat()


def print_groups(groups: list[QueryGroup]) -> None:
    for group in groups:
        print(f"{group.name}")
        print(f"  {group.description}")
        print(f"  {group.query}")
        print()


def main() -> None:
    args = parse_args()
    groups = select_groups(args.group)

    if args.list_groups:
        print_groups(groups)
        return

    papers, matched_groups, cutoff = gather_recent_papers(
        groups=groups,
        days=args.days,
        per_query=args.per_query,
        strict=args.strict,
    )

    print(f"Math formalization weekly collection")
    print(f"Window: {cutoff} to {datetime.now(timezone.utc).date().isoformat()} (UTC)")
    print(f"Groups: {', '.join(group.name for group in groups)}")
    print(f"Strict filter: {'on' if args.strict else 'off'}")
    print(f"Candidates: {len(papers)}")
    print()

    print("Queries:")
    for group in groups:
        print(f"- {group.name}: {group.description}")
        print(f"  {group.query}")
    print()

    for paper in papers:
        labels = ", ".join(sorted(matched_groups[paper.arxiv_id]))
        print(f"[{paper.arxiv_id}] {paper.title}")
        print(
            f"  {paper.published.strftime('%Y-%m-%d')} | "
            f"{paper.primary_category} | "
            f"groups: {labels}"
        )
        print(f"  {paper.url}")
        if args.verbose and paper.summary:
            print(f"  {format_excerpt(paper.summary)}")
        print()


if __name__ == "__main__":
    main()
