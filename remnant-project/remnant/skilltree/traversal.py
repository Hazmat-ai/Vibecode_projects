"""
skilltree/traversal.py — BFS/DFS traversal helpers for SkillGraph.
All algorithms work without networkx.
"""

from typing import List, Set, TYPE_CHECKING
from collections import deque

if TYPE_CHECKING:
    from skilltree.graph import SkillGraph
    from core.models import Skill


def find_unlockable(graph: "SkillGraph", known: Set[str]) -> List["Skill"]:
    """Wrapper: return skills unlockable given current known set."""
    return graph.get_unlockable(known)


def find_blocking(graph: "SkillGraph", target_id: str, known: Set[str]) -> List["Skill"]:
    """Wrapper: return skills blocking immediate unlock of target."""
    return graph.get_blocking(target_id, known)


def path_to_skill(graph: "SkillGraph", known: Set[str], target_id: str) -> List["Skill"]:
    """Wrapper: return ordered skill list to reach target_id."""
    return graph.shortest_path(known, target_id)


def critical_path(graph: "SkillGraph", known: Set[str], steps: int = 5) -> List["Skill"]:
    """
    Return the highest-CS skills reachable within `steps` learning moves.
    BFS layer by layer; each layer is the set of newly unlockable skills.
    """
    all_reachable = []
    current_known = set(known)
    for _ in range(steps):
        unlockable = graph.get_unlockable(current_known)
        if not unlockable:
            break
        best = max(unlockable, key=lambda s: s.civilization_score)
        all_reachable.append(best)
        current_known.add(best.id)
    return all_reachable
