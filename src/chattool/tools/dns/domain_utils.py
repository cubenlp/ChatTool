from __future__ import annotations


def split_full_domain(full_domain: str) -> tuple[str, str]:
    parts = full_domain.split(".")
    if len(parts) < 2:
        raise ValueError("invalid full domain")
    domain = ".".join(parts[-2:])
    rr_parts = parts[:-2]
    rr = "@" if not rr_parts else ".".join(rr_parts)
    return domain, rr
