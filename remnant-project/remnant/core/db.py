"""
core/db.py — SQLite interface for REMNANT.
All data lives in a single .db file. This module owns schema creation and migration.
"""

import sqlite3
import json
import os
from typing import Optional
from datetime import date


SCHEMA_VERSION = "2"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    domain TEXT NOT NULL,
    tags TEXT NOT NULL,
    civilization_score INTEGER NOT NULL,
    difficulty INTEGER NOT NULL,
    requires_skills TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    sources TEXT NOT NULL,
    last_updated TEXT,
    custom INTEGER NOT NULL DEFAULT 0
);

CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    id UNINDEXED,
    title,
    summary,
    content,
    tags,
    content='articles',
    content_rowid='rowid'
);

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    domain TEXT NOT NULL,
    civilization_score INTEGER NOT NULL,
    requires TEXT NOT NULL,
    unlocks TEXT NOT NULL,
    summary TEXT NOT NULL,
    difficulty INTEGER NOT NULL,
    time_to_learn_days INTEGER NOT NULL,
    custom INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS communities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    known_skills TEXT NOT NULL DEFAULT '[]',
    created_at TEXT,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL,
    record_id TEXT NOT NULL,
    local_value TEXT NOT NULL,
    remote_value TEXT NOT NULL,
    detected_at TEXT NOT NULL
);
"""

_FTS_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS articles_fts_insert;
DROP TRIGGER IF EXISTS articles_fts_update;
DROP TRIGGER IF EXISTS articles_fts_delete;
CREATE TRIGGER articles_fts_insert AFTER INSERT ON articles BEGIN
 INSERT INTO articles_fts(rowid,id,title,summary,content,tags)
 VALUES(new.rowid,new.id,new.title,new.summary,new.content,new.tags);
END;
CREATE TRIGGER articles_fts_update AFTER UPDATE ON articles BEGIN
 INSERT INTO articles_fts(articles_fts,rowid,id,title,summary,content,tags)
 VALUES('delete',old.rowid,old.id,old.title,old.summary,old.content,old.tags);
 INSERT INTO articles_fts(rowid,id,title,summary,content,tags)
 VALUES(new.rowid,new.id,new.title,new.summary,new.content,new.tags);
END;
CREATE TRIGGER articles_fts_delete AFTER DELETE ON articles BEGIN
 INSERT INTO articles_fts(articles_fts,rowid,id,title,summary,content,tags)
 VALUES('delete',old.rowid,old.id,old.title,old.summary,old.content,old.tags);
END;
"""


class Database:
    """Main database interface. Pass ':memory:' for testing."""

    def __init__(self, path: str = "data/remnant.db"):
        self.path = path
        if path != ":memory:":
            os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        self._conn = sqlite3.connect(path, timeout=5)
        if path != ":memory:":
            os.chmod(path, 0o600)
        self._transaction_depth = 0
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._initialize()

    # ------------------------------------------------------------------ #
    #  Schema management                                                   #
    # ------------------------------------------------------------------ #

    def _initialize(self):
        # Reject unknown future schemas before mutating an existing database.
        tables = {r[0] for r in self._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        version = None
        if "meta" in tables:
            row = self._conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            version = row[0] if row else None
            if version not in (None, "1", SCHEMA_VERSION):
                raise ValueError("Unsupported database schema version: {}".format(version))
        self.fts_available = True
        schema = _SCHEMA_SQL
        try:
            self._conn.executescript(schema)
        except sqlite3.OperationalError as error:
            if "no such module: fts5" not in str(error).lower():
                raise
            self.fts_available = False
            start = schema.index("CREATE VIRTUAL TABLE")
            end = schema.index("CREATE TABLE IF NOT EXISTS skills", start)
            self._conn.executescript(schema[:start] + schema[end:])
        if self.fts_available:
            self._conn.executescript(_FTS_TRIGGER_SQL)
            if version != SCHEMA_VERSION:
                self._conn.execute("INSERT INTO articles_fts(articles_fts) VALUES('rebuild')")
        self._conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)", (SCHEMA_VERSION,))
        self._conn.commit()

    def _commit(self):
        if not self._transaction_depth:
            self._conn.commit()

    def transaction(self):
        from contextlib import contextmanager
        @contextmanager
        def atomic():
            if self._transaction_depth:
                raise RuntimeError("Nested transactions are not supported.")
            self._conn.execute("BEGIN IMMEDIATE")
            self._transaction_depth += 1
            try:
                yield self
                self._conn.commit()
            except BaseException:
                self._conn.rollback()
                raise
            finally:
                self._transaction_depth -= 1
        return atomic()

    def backup(self, output_path):
        import pathlib
        import tempfile
        target = pathlib.Path(output_path).resolve()
        if self.path != ":memory:" and target == pathlib.Path(self.path).resolve():
            raise ValueError("Backup target must differ from the live database.")
        if target.exists():
            raise ValueError("Backup target already exists; choose a new path.")
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".remnant-backup-", dir=str(target.parent))
        os.close(descriptor)
        try:
            connection = sqlite3.connect(temporary)
            try:
                self._conn.backup(connection)
            finally:
                connection.close()
            # Exclusive hard-link creation prevents replacing an existing target.
            os.link(temporary, str(target))
        finally:
            os.unlink(temporary)


    def get_meta(self, key: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def set_meta(self, key: str, value: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, value)
        )
        self._commit()

    # ------------------------------------------------------------------ #
    #  Article CRUD                                                        #
    # ------------------------------------------------------------------ #

    def insert_article(self, article, replace: bool = False) -> bool:
        """Insert an Article dataclass. Returns True if inserted, False if skipped."""
        from core.validation import validate_record
        validate_record(article)
        if replace:
            existing = self.get_article(article.id)
            if existing and existing.custom and not article.custom:
                return False
        values = self._article_to_row(article)
        if replace and self.get_article(article.id):
            cur = self._conn.execute("UPDATE articles SET title=?,domain=?,tags=?,civilization_score=?,difficulty=?,requires_skills=?,summary=?,content=?,sources=?,last_updated=?,custom=? WHERE id=?", values[1:] + (values[0],))
        else:
            cur = self._conn.execute("INSERT OR IGNORE INTO articles VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", values)
        self._commit()
        return cur.rowcount > 0

    def get_article(self, article_id: str):
        row = self._conn.execute(
            "SELECT * FROM articles WHERE id=?", (article_id,)
        ).fetchone()
        return self._row_to_article(row) if row else None

    def list_articles(
        self,
        domain: Optional[str] = None,
        min_cs: int = 0,
        limit: int = 50,
        offset: int = 0,
    ):
        q = "SELECT * FROM articles WHERE civilization_score >= ?"
        params = [min_cs]
        if domain:
            q += " AND domain=?"
            params.append(domain)
        q += " ORDER BY civilization_score DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self._conn.execute(q, params).fetchall()
        return [self._row_to_article(r) for r in rows]

    def search_articles(self, query: str, domain: Optional[str] = None, limit: int = 20, min_cs: int = 0):
        """Full-text search via FTS5."""
        if not self.fts_available:
            raise sqlite3.OperationalError("FTS5 unavailable")
        query = " AND ".join('"' + term.replace('"', '""') + '"*' for term in query.split())
        if not query:
            return []
        q = """
            SELECT a.* FROM articles a
            JOIN articles_fts fts ON a.rowid = fts.rowid
            WHERE articles_fts MATCH ? AND a.civilization_score >= ?
        """
        params = [query, min_cs]
        if domain:
            q += " AND a.domain=?"
            params.append(domain)
        q += " ORDER BY a.civilization_score DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(q, params).fetchall()
        return [self._row_to_article(r) for r in rows]

    # ------------------------------------------------------------------ #
    #  Skill CRUD                                                          #
    # ------------------------------------------------------------------ #

    def insert_skill(self, skill, replace: bool = False) -> bool:
        from core.validation import validate_record
        validate_record(skill)
        existing = self.get_skill(skill.id)
        if replace and existing and existing.custom and not skill.custom:
            return False
        cmd = "INSERT OR REPLACE" if replace else "INSERT OR IGNORE"
        cur = self._conn.execute(
            f"{cmd} INTO skills VALUES(?,?,?,?,?,?,?,?,?,?)",
            self._skill_to_row(skill),
        )
        self._commit()
        return cur.rowcount > 0

    def get_skill(self, skill_id: str):
        row = self._conn.execute(
            "SELECT * FROM skills WHERE id=?", (skill_id,)
        ).fetchone()
        return self._row_to_skill(row) if row else None

    def list_skills(
        self,
        domain: Optional[str] = None,
        min_cs: int = 0,
        limit: int = 100,
    ):
        q = "SELECT * FROM skills WHERE civilization_score >= ?"
        params = [min_cs]
        if domain:
            q += " AND domain=?"
            params.append(domain)
        q += " ORDER BY civilization_score DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(q, params).fetchall()
        return [self._row_to_skill(r) for r in rows]

    def all_skills(self):
        rows = self._conn.execute("SELECT * FROM skills").fetchall()
        return [self._row_to_skill(r) for r in rows]

    # ------------------------------------------------------------------ #
    #  Community CRUD                                                      #
    # ------------------------------------------------------------------ #

    def insert_community(self, community) -> bool:
        from core.validation import validate_community
        validate_community(community)
        cur = self._conn.execute(
            "INSERT OR IGNORE INTO communities(id,name,known_skills,created_at,notes) "
            "VALUES(?,?,?,?,?)",
            (
                community.id,
                community.name,
                json.dumps(community.known_skills),
                community.created_at.isoformat() if community.created_at else None,
                community.notes,
            ),
        )
        self._commit()
        return cur.rowcount > 0

    def get_community(self, community_id: str):
        row = self._conn.execute(
            "SELECT * FROM communities WHERE id=?", (community_id,)
        ).fetchone()
        return self._row_to_community(row) if row else None

    def list_communities(self):
        rows = self._conn.execute("SELECT * FROM communities ORDER BY name").fetchall()
        return [self._row_to_community(r) for r in rows]

    def update_community_skills(self, community_id: str, known_skills):
        self._conn.execute(
            "UPDATE communities SET known_skills=? WHERE id=?",
            (json.dumps(sorted(set(known_skills))), community_id),
        )
        self._commit()

    # ------------------------------------------------------------------ #
    #  Sync conflicts                                                      #
    # ------------------------------------------------------------------ #

    def insert_conflict(self, record_type: str, record_id: str, local_val: str, remote_val: str):
        from datetime import datetime, timezone
        existing = self._conn.execute("SELECT 1 FROM sync_conflicts WHERE record_type=? AND record_id=? AND local_value=? AND remote_value=?", (record_type, record_id, local_val, remote_val)).fetchone()
        if existing:
            return False
        self._conn.execute(
            "INSERT INTO sync_conflicts(record_type,record_id,local_value,remote_value,detected_at) "
            "VALUES(?,?,?,?,?)",
            (record_type, record_id, local_val, remote_val, datetime.now(timezone.utc).isoformat()),
        )
        self._commit()
        return True

    def list_conflicts(self):
        return self._conn.execute(
            "SELECT * FROM sync_conflicts ORDER BY detected_at DESC"
        ).fetchall()

    # ------------------------------------------------------------------ #
    #  Raw connection access (for sync module)                            #
    # ------------------------------------------------------------------ #

    @property
    def connection(self):
        return self._conn

    def close(self):
        self._conn.close()

    # ------------------------------------------------------------------ #
    #  Row<->dataclass conversion helpers                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _article_to_row(a):
        from datetime import date as date_type
        return (
            a.id,
            a.title,
            a.domain,
            json.dumps(a.tags),
            a.civilization_score,
            a.difficulty,
            json.dumps(a.requires_skills),
            a.summary,
            a.content,
            json.dumps(a.sources),
            a.last_updated.isoformat() if isinstance(a.last_updated, date_type) else a.last_updated,
            int(a.custom),
        )

    @staticmethod
    def _row_to_article(row):
        from core.models import Article
        from datetime import date as date_type
        if type(row["custom"]) is not int or row["custom"] not in (0, 1):
            raise ValueError("Invalid custom flag.")
        lu = row["last_updated"]
        return Article(
            id=row["id"],
            title=row["title"],
            domain=row["domain"],
            tags=json.loads(row["tags"]),
            civilization_score=row["civilization_score"],
            difficulty=row["difficulty"],
            requires_skills=json.loads(row["requires_skills"]),
            summary=row["summary"],
            content=row["content"],
            sources=json.loads(row["sources"]),
            last_updated=date_type.fromisoformat(lu) if lu else None,
            custom=bool(row["custom"]),
        )

    @staticmethod
    def _skill_to_row(s):
        return (
            s.id,
            s.title,
            s.domain,
            s.civilization_score,
            json.dumps(s.requires),
            json.dumps(s.unlocks),
            s.summary,
            s.difficulty,
            s.time_to_learn_days,
            int(s.custom),
        )

    @staticmethod
    def _row_to_skill(row):
        from core.models import Skill
        if type(row["custom"]) is not int or row["custom"] not in (0, 1):
            raise ValueError("Invalid custom flag.")
        return Skill(
            id=row["id"],
            title=row["title"],
            domain=row["domain"],
            civilization_score=row["civilization_score"],
            requires=json.loads(row["requires"]),
            unlocks=json.loads(row["unlocks"]),
            summary=row["summary"],
            difficulty=row["difficulty"],
            time_to_learn_days=row["time_to_learn_days"],
            custom=bool(row["custom"]),
        )

    @staticmethod
    def _row_to_community(row):
        from core.models import Community
        from datetime import date as date_type
        ca = row["created_at"]
        return Community(
            id=row["id"],
            name=row["name"],
            known_skills=json.loads(row["known_skills"]),
            created_at=date_type.fromisoformat(ca) if ca else None,
            notes=row["notes"],
        )
