"""
library/scorer.py — Civilization Score (CS) calculation.
CS blends a hand-curated base score with a graph-derived dependency bonus.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skilltree.graph import SkillGraph


def compute_skill_cs(skill_id: str, graph: "SkillGraph") -> int:
    """
    Compute final Civilization Score for a skill.
    Base score + up to 20 bonus points from dependent count, capped at 100.
    """
    skill = graph.get_skill(skill_id)
    if skill is None:
        return 0
    base = skill.civilization_score
    dependents = len(graph.get_dependents(skill_id))
    dependency_bonus = min(20, dependents * 2)
    return min(100, base + dependency_bonus)


def score_article(article) -> int:
    """
    Articles use their stored civilization_score as-is.
    Future versions may blend additional factors here.
    """
    return article.civilization_score
