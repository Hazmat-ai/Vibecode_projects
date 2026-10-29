"""
core/models.py — Canonical data structures for REMNANT.
Match these exactly; do not extend without updating AGENT_CONTEXT.md and the DB schema.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class Article:
    id: str                          # kebab-case slug, globally unique
    title: str
    domain: str                      # food | medicine | engineering | governance | energy | communication | other
    tags: List[str]
    civilization_score: int          # 0-100
    difficulty: int                  # 1-5
    requires_skills: List[str]       # list of skill IDs
    summary: str                     # 1-3 sentence plain text summary
    content: str                     # full markdown content
    sources: List[str]
    last_updated: Optional[date] = None
    custom: bool = False             # True if user-added, False if from seed data

    def __post_init__(self):
        from core.validation import validate_record
        validate_record(self)


@dataclass
class Skill:
    id: str                          # kebab-case slug, globally unique
    title: str
    domain: str
    civilization_score: int          # 0-100
    requires: List[str]              # list of skill IDs that must be known first
    unlocks: List[str]               # list of skill IDs this makes available (denormalized cache)
    summary: str
    difficulty: int                  # 1-5
    time_to_learn_days: int
    custom: bool = False

    def __post_init__(self):
        from core.validation import validate_record
        validate_record(self)


@dataclass
class Community:
    id: str                          # user-chosen name/slug
    name: str
    known_skills: List[str] = field(default_factory=list)   # list of skill IDs
    created_at: Optional[date] = None
    notes: str = ""

    def __post_init__(self):
        from core.validation import validate_community
        validate_community(self)
