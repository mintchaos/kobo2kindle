from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


def find_books(
    query: str,
    books: list[Any],
    threshold: float = 0.3,
    max_results: int = 5,
) -> list[tuple[Any, float]]:
    """Find books matching a query string, ranked by relevance.

    Each book must have a .Title attribute.
    Returns list of (book, score) tuples, highest score first.
    """
    query_lower = query.lower()
    scored = []

    for book in books:
        title_lower = book.Title.lower()

        if query_lower in title_lower:
            # Substring matches always rank above fuzzy matches.
            # Scale from 0.7 (short query in long title) to 1.0 (exact match).
            ratio = len(query_lower) / len(title_lower)
            score = 0.7 + 0.3 * ratio
        else:
            # Fuzzy match tops out below 0.7 so substring matches always win.
            score = SequenceMatcher(None, query_lower, title_lower).ratio()
            score = min(score, 0.69)

        scored.append((book, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [(book, score) for book, score in scored[:max_results] if score >= threshold]
