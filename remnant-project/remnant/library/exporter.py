"""
library/exporter.py — Export articles to .txt or .md files.
All output is plain ASCII/UTF-8; no binary formats.
"""

import os
import sys
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.models import Article

_SUPPORTS_UTF8 = sys.stdout.encoding and sys.stdout.encoding.lower() in ("utf-8", "utf8")


def export_article(
    article: "Article",
    fmt: str = "txt",
    output_path: Optional[str] = None,
) -> str:
    """
    Export an article to a string and optionally write to a file.
    fmt: 'txt' | 'md'
    Returns the exported string.
    """
    if fmt == "md":
        text = _to_markdown(article)
    else:
        text = _to_plaintext(article)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    return text


def _to_plaintext(article: "Article") -> str:
    sep = "=" * 60
    difficulty_bar = '*' * article.difficulty + '-' * (5 - article.difficulty)
    lines = [
        sep,
        article.title,
        sep,
        f"Domain: {article.domain}  |  Civilization Score: {article.civilization_score}/100",
        f"Difficulty: [{difficulty_bar}] ({article.difficulty}/5)",
        f"Tags: {', '.join(article.tags)}",
        "",
        "SUMMARY",
        "-" * 40,
        article.summary,
        "",
        "CONTENT",
        "-" * 40,
        article.content,
    ]
    if article.sources:
        lines += ["", "SOURCES", "-" * 40]
        for s in article.sources:
            lines.append(f"  - {s}")
    if article.requires_skills:
        lines += ["", f"Requires skills: {', '.join(article.requires_skills)}"]
    lines.append(sep)
    return "\n".join(lines)


def _to_markdown(article: "Article") -> str:
    lines = [
        f"# {article.title}",
        "",
        f"**Domain:** {article.domain} | **Civilization Score:** {article.civilization_score}/100 | **Difficulty:** {article.difficulty}/5",
        "",
        f"**Tags:** {', '.join(article.tags)}",
        "",
        "## Summary",
        "",
        article.summary,
        "",
        "## Content",
        "",
        article.content,
    ]
    if article.requires_skills:
        lines += ["", f"**Requires skills:** {', '.join(article.requires_skills)}"]
    if article.sources:
        lines += ["", "## Sources", ""]
        for s in article.sources:
            lines.append(f"- {s}")
    return "\n".join(lines)
