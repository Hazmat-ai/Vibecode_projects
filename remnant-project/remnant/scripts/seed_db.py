"""
scripts/seed_db.py — Populate the REMNANT database from seed YAML files.
Run once after cloning: python scripts/seed_db.py
Run with --update to re-import changed files without wiping custom entries.
Uses stdlib-only YAML loader — no pyyaml required.
"""

import sys
import os
import argparse
from datetime import date, datetime, timezone

# Ensure the remnant package dir is on path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from core.db import Database
from core.models import Article, Skill
from core.yaml_loader import load_file
from config import DEFAULT_DB_PATH, SEED_ARTICLES_DIR, SEED_SKILLS_DIR


def load_article_from_yaml(path: str) -> Article:
    data = load_file(path)
    lu = data.get("last_updated")
    if isinstance(lu, str):
        try:
            lu = date.fromisoformat(lu)
        except ValueError:
            lu = None
    return Article(
        id=data["id"],
        title=data["title"],
        domain=data.get("domain", "other"),
        tags=data.get("tags") or [],
        civilization_score=int(data.get("civilization_score", 50)),
        difficulty=int(data.get("difficulty", 3)),
        requires_skills=data.get("requires_skills") or [],
        summary=(data.get("summary") or "").strip(),
        content=(data.get("content") or "").strip(),
        sources=data.get("sources") or [],
        last_updated=lu,
        custom=False,
    )


def load_skill_from_yaml(path: str) -> Skill:
    data = load_file(path)
    return Skill(
        id=data["id"],
        title=data["title"],
        domain=data.get("domain", "other"),
        civilization_score=int(data.get("civilization_score", 50)),
        requires=data.get("requires") or [],
        unlocks=data.get("unlocks") or [],
        summary=(data.get("summary") or "").strip(),
        difficulty=int(data.get("difficulty", 3)),
        time_to_learn_days=int(data.get("time_to_learn_days", 0)),
        custom=False,
    )


def _seed(db: Database, update: bool = False):
    articles_added = 0
    articles_skipped = 0
    skills_added = 0
    skills_skipped = 0
    errors = []

    # --- Articles ---
    if os.path.isdir(SEED_ARTICLES_DIR):
        for filename in sorted(os.listdir(SEED_ARTICLES_DIR)):
            if not filename.endswith(".yaml"):
                continue
            path = os.path.join(SEED_ARTICLES_DIR, filename)
            try:
                article = load_article_from_yaml(path)
                added = db.insert_article(article, replace=update)
                if added:
                    articles_added += 1
                    print(f"  + article: {article.id}")
                else:
                    articles_skipped += 1
            except Exception as e:
                errors.append(f"[article] {filename}: {e}")
    else:
        print(f"  [WARN] Articles directory not found: {SEED_ARTICLES_DIR}")

    # --- Skills ---
    if os.path.isdir(SEED_SKILLS_DIR):
        for filename in sorted(os.listdir(SEED_SKILLS_DIR)):
            if not filename.endswith(".yaml"):
                continue
            path = os.path.join(SEED_SKILLS_DIR, filename)
            try:
                skill = load_skill_from_yaml(path)
                added = db.insert_skill(skill, replace=update)
                if added:
                    skills_added += 1
                    print(f"  + skill:   {skill.id}")
                else:
                    skills_skipped += 1
            except Exception as e:
                errors.append(f"[skill] {filename}: {e}")
    else:
        print(f"  [WARN] Skills directory not found: {SEED_SKILLS_DIR}")

    # Set seed metadata
    db.set_meta("seed_version", datetime.now(timezone.utc).isoformat())

    return {
        "articles_added": articles_added,
        "articles_skipped": articles_skipped,
        "skills_added": skills_added,
        "skills_skipped": skills_skipped,
        "errors": errors,
    }


def seed(db: Database, update: bool = False):
    from skilltree.graph import SkillGraph
    with db.transaction():
        result = _seed(db, update=update)
        if result["errors"]:
            raise ValueError("Seed import rejected: " + "; ".join(result["errors"]))
        SkillGraph(db)
    return result


def main():
    parser = argparse.ArgumentParser(description="Seed the REMNANT database from YAML files.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to remnant.db")
    parser.add_argument("--update", action="store_true",
                        help="Replace existing seed records (preserves custom entries)")
    args = parser.parse_args()

    print(f"Seeding database: {args.db}")
    db = Database(args.db)
    result = seed(db, update=args.update)
    db.close()

    print()
    print(f"Done.")
    print(f"  Articles: +{result['articles_added']} added, {result['articles_skipped']} skipped")
    print(f"  Skills:   +{result['skills_added']} added, {result['skills_skipped']} skipped")
    if result["errors"]:
        print(f"  Errors ({len(result['errors'])}):")
        for e in result["errors"]:
            print(f"    {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
