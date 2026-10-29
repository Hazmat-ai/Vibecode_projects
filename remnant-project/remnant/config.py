"""
config.py — App-wide settings and constants for REMNANT.
"""

import os

# Default database path (relative to the remnant/ package dir or from CWD)
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "remnant.db"
)

# Seed data directories
SEED_ARTICLES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "seed", "articles"
)
SEED_SKILLS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "seed", "skills"
)

# Valid article/skill domains
DOMAINS = [
    "food",
    "medicine",
    "engineering",
    "governance",
    "energy",
    "communication",
    "other",
]

# Exit codes
EXIT_OK = 0
EXIT_USER_ERROR = 1
EXIT_INTERNAL_ERROR = 2
EXIT_NOT_FOUND = 3

# Schema version
SCHEMA_VERSION = "1"

# Display defaults
DEFAULT_TOP_LIMIT = 20
DEFAULT_SEARCH_LIMIT = 20
TERMINAL_WIDTH = 72
