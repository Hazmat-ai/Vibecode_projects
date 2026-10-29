"""Runtime contracts shared by local imports and offline database merges."""
import re
import unicodedata
from datetime import date

DOMAINS = {"food", "medicine", "engineering", "governance", "energy", "communication", "other"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

def text(value, name, maximum=200, empty=False):
    if not isinstance(value, str) or len(value) > maximum or (not empty and not value.strip()):
        raise ValueError("{} must be text of at most {} characters.".format(name, maximum))
    if any(unicodedata.category(c) == "Cc" and c not in "\n\t\r" for c in value):
        raise ValueError("{} contains terminal control characters.".format(name))
    return value

def slug(value):
    text(value, "id", 100)
    if not SLUG.fullmatch(value):
        raise ValueError("IDs must be lowercase words separated by hyphens.")

def number(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("{} must be an integer from {} to {}.".format(name, low, high))

def strings(values, name, ids=False):
    if not isinstance(values, list) or len(values) > 100:
        raise ValueError("{} must be a list of at most 100 strings.".format(name))
    for value in values:
        text(value, name, 1000)
        if ids:
            slug(value)
    if len(values) != len(set(values)):
        raise ValueError("{} contains duplicates.".format(name))

def validate_record(record):
    slug(record.id)
    text(record.title, "title")
    text(record.domain, "domain", 50)
    if record.domain not in DOMAINS:
        raise ValueError("Unsupported knowledge domain.")
    number(record.civilization_score, "civilization_score", 0, 100)
    number(record.difficulty, "difficulty", 1, 5)
    text(record.summary, "summary", 5000)
    if type(record.custom) is not bool:
        raise ValueError("custom must be a boolean.")
    if hasattr(record, "content"):
        text(record.content, "content", 200000)
        strings(record.tags, "tags")
        strings(record.requires_skills, "requires_skills", ids=True)
        strings(record.sources, "sources")
        if record.last_updated is not None and not isinstance(record.last_updated, date):
            raise ValueError("last_updated must be a date.")
    else:
        strings(record.requires, "requires", ids=True)
        strings(record.unlocks, "unlocks", ids=True)
        number(record.time_to_learn_days, "time_to_learn_days", 0, 36500)

def validate_community(record):
    slug(record.id)
    text(record.name, "community name")
    text(record.notes, "notes", 10000, empty=True)
    strings(record.known_skills, "known_skills", ids=True)
    if record.created_at is not None and not isinstance(record.created_at, date):
        raise ValueError("created_at must be a date.")
