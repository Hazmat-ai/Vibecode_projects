"""
core/search.py — Full-text search via SQLite FTS5.
Delegates to db.py's search_articles; this module provides higher-level helpers.
"""

from typing import List, Optional, TYPE_CHECKING
import sqlite3

if TYPE_CHECKING:
    from core.db import Database
    from core.models import Article


def search_library(
    db: "Database",
    query: str,
    domain: Optional[str] = None,
    limit: int = 20,
    min_cs: int = 0,
) -> List["Article"]:
    """
    Full-text search across article title, summary, content, and tags.
    Falls back to a LIKE-based search if FTS5 is unavailable.
    Returns results sorted by civilization_score descending.
    """
    query = query.strip()
    if not query:
        return []
    if not 1 <= limit <= 1000 or not 0 <= min_cs <= 100:
        raise ValueError("Search limit or score is out of range.")
    # Try FTS5 first
    try:
        results = db.search_articles(query, domain=domain, limit=limit, min_cs=min_cs)
    except sqlite3.OperationalError:
        # Fallback: simple LIKE search
        results = _like_search(db, query, domain=domain, limit=limit, min_cs=min_cs)

    return results


def _like_search(db: "Database", query: str, domain: Optional[str], limit: int, min_cs: int = 0):
    """Simple LIKE-based fallback search (no FTS5 required)."""
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    q = """
        SELECT * FROM articles
        WHERE civilization_score >= ? AND (title LIKE ? ESCAPE '\\' OR summary LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\' OR tags LIKE ? ESCAPE '\\')
    """
    params = [min_cs, pattern, pattern, pattern, pattern]
    if domain:
        q += " AND domain=?"
        params.append(domain)
    q += " ORDER BY civilization_score DESC LIMIT ?"
    params.append(limit)
    rows = db.connection.execute(q, params).fetchall()
    return [db._row_to_article(r) for r in rows]
