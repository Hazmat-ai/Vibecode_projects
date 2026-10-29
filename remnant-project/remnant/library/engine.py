"""
library/engine.py — Article retrieval, ranking, and filtering.
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.db import Database
    from core.models import Article


def get_article(db: "Database", id_or_title: str) -> Optional["Article"]:
    """Retrieve article by exact ID first, then case-insensitive title match."""
    article = db.get_article(id_or_title)
    if article:
        return article
    # Title fallback
    rows = db.connection.execute(
        "SELECT * FROM articles WHERE LOWER(title)=?", (id_or_title.lower(),)
    ).fetchall()
    if rows:
        return db._row_to_article(rows[0])
    return None


def top_articles(
    db: "Database",
    limit: int = 20,
    domain: Optional[str] = None,
    min_cs: int = 0,
) -> List["Article"]:
    """Return top articles sorted by Civilization Score."""
    return db.list_articles(domain=domain, min_cs=min_cs, limit=limit)


def list_domains(db: "Database") -> List[str]:
    """Return all distinct domains present in the articles table."""
    rows = db.connection.execute(
        "SELECT DISTINCT domain FROM articles ORDER BY domain"
    ).fetchall()
    return [r[0] for r in rows]
