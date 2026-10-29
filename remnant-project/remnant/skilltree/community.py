"""
skilltree/community.py — Manage community known/owned skill state.
"""

from datetime import date
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.db import Database
    from core.models import Community


def create_community(db: "Database", name: str) -> "Community":
    from core.models import Community
    import re
    community_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not community_id or not name.strip():
        raise ValueError("Community name must contain a letter or digit.")
    community = Community(
        id=community_id,
        name=name,
        known_skills=[],
        created_at=date.today(),
        notes="",
    )
    if not db.insert_community(community):
        raise ValueError(f"Community '{community_id}' already exists.")
    return community


def learn_skill(db: "Database", community_id: str, skill_id: str) -> bool:
    """Add skill_id to community's known set. Returns True if it was newly learned."""
    community = db.get_community(community_id)
    if not community:
        raise ValueError(f"Community '{community_id}' not found.")
    skill = db.get_skill(skill_id)
    if skill is None:
        raise ValueError("Unknown skill: " + skill_id)
    if skill_id in community.known_skills:
        return False
    missing = sorted(set(skill.requires) - set(community.known_skills))
    if missing:
        raise ValueError("Learn prerequisites first: " + ", ".join(missing))
    community.known_skills.append(skill_id)
    db.update_community_skills(community_id, community.known_skills)
    return True


def unlearn_skill(db: "Database", community_id: str, skill_id: str) -> bool:
    """Remove skill_id from community's known set. Returns True if it was present."""
    community = db.get_community(community_id)
    if not community:
        raise ValueError(f"Community '{community_id}' not found.")
    if skill_id not in community.known_skills:
        return False
    dependents = [s.id for s in db.all_skills() if s.id in community.known_skills and skill_id in s.requires]
    if dependents:
        raise ValueError("Remove dependent skills first: " + ", ".join(sorted(dependents)))
    community.known_skills.remove(skill_id)
    db.update_community_skills(community_id, community.known_skills)
    return True


def get_community(db: "Database", community_id: str) -> Optional["Community"]:
    return db.get_community(community_id)


def list_communities(db: "Database") -> List["Community"]:
    return db.list_communities()
