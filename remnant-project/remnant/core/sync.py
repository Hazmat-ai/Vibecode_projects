"""Validated, read-only source ingestion with one atomic local merge."""
import json
import os
import pathlib
import sqlite3

MAX_ROWS = 10000
MAX_DATABASE_BYTES = 64 * 1024 * 1024
COLUMNS = {
    "articles": ("id", "title", "domain", "tags", "civilization_score", "difficulty", "requires_skills", "summary", "content", "sources", "last_updated", "custom"),
    "skills": ("id", "title", "domain", "civilization_score", "requires", "unlocks", "summary", "difficulty", "time_to_learn_days", "custom"),
    "communities": ("id", "name", "known_skills", "created_at", "notes"),
}

def merge_databases(local_db, source_path):
    from skilltree.graph import validate_dependencies
    source = pathlib.Path(source_path).resolve()
    if not source.is_file() or source.stat().st_size > MAX_DATABASE_BYTES:
        raise RuntimeError("Source must be an existing database smaller than 64 MiB.")
    if local_db.path != ":memory:" and source == pathlib.Path(local_db.path).resolve():
        raise RuntimeError("Cannot merge a database into itself.")
    connection = None
    try:
        connection = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA query_only=ON")
        # Bound work even for pathological/corrupt schemas supplied over USB.
        budget = [10000]
        def progress():
            budget[0] -= 1
            return int(budget[0] <= 0)
        connection.set_progress_handler(progress, 1000)
        schema = connection.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        if not schema or schema[0] not in ("1", "2"):
            raise ValueError("Unsupported source schema version.")
        loaded = {}
        for table, columns in COLUMNS.items():
            kind = connection.execute("SELECT type FROM sqlite_master WHERE name=?", (table,)).fetchone()
            if not kind or kind[0] != "table":
                raise ValueError("Source is missing a required ordinary table: " + table)
            sql = 'SELECT ' + ','.join('"'+c+'"' for c in columns) + ' FROM ' + table + ' LIMIT ?'
            rows = connection.execute(sql, (MAX_ROWS + 1,)).fetchall()
            if len(rows) > MAX_ROWS:
                raise ValueError("Source table exceeds the row limit.")
            convert = {"articles": local_db._row_to_article, "skills": local_db._row_to_skill, "communities": local_db._row_to_community}[table]
            loaded[table] = [convert(row) for row in rows]
            if len({record.id for record in loaded[table]}) != len(rows):
                raise ValueError("Duplicate record IDs in source.")
        summary = {"articles_added": 0, "skills_added": 0, "conflicts": 0, "communities_merged": 0}
        with local_db.transaction():
            skills = {s.id: s for s in local_db.all_skills()}
            for skill in loaded["skills"]:
                skills.setdefault(skill.id, skill)
            validate_dependencies(skills)
            for article in loaded["articles"]:
                if any(req not in skills for req in article.requires_skills):
                    raise ValueError("Article references an unknown skill: " + article.id)
                current = local_db.get_article(article.id)
                if current is None:
                    local_db.insert_article(article)
                    summary["articles_added"] += 1
                elif current != article:
                    if local_db.insert_conflict("article", article.id, json.dumps(local_db._article_to_row(current)), json.dumps(local_db._article_to_row(article))):
                        summary["conflicts"] += 1
            for skill in loaded["skills"]:
                current = local_db.get_skill(skill.id)
                if current is None:
                    local_db.insert_skill(skill)
                    summary["skills_added"] += 1
                elif current != skill:
                    if local_db.insert_conflict("skill", skill.id, json.dumps(local_db._skill_to_row(current)), json.dumps(local_db._skill_to_row(skill))):
                        summary["conflicts"] += 1
            for community in loaded["communities"]:
                if any(skill not in skills for skill in community.known_skills):
                    raise ValueError("Community references an unknown skill.")
                known = set(community.known_skills)
                if any(not set(skills[key].requires) <= known for key in known):
                    raise ValueError("Community has unmet skill prerequisites.")
                current = local_db.get_community(community.id)
                if current is None:
                    local_db.insert_community(community)
                    summary["communities_merged"] += 1
                else:
                    merged = set(current.known_skills) | set(community.known_skills)
                    if merged != set(current.known_skills):
                        local_db.update_community_skills(current.id, merged)
                        summary["communities_merged"] += 1
        return summary
    except (sqlite3.Error, ValueError, TypeError, KeyError, OSError) as error:
        raise RuntimeError("Merge rejected; local data was not changed: {}".format(error)) from error
    finally:
        if connection is not None:
            connection.close()
