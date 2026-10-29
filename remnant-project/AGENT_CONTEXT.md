# REMNANT development context

The current architecture and CLI contracts are documented in README.md. Root AGENT_CONTEXT.md also applies.

- Python 3.8-compatible, offline, terminal-only, zero mandatory third-party packages.
- main.py uses argparse. Keep --db / --ui before the subcommand, and preserve scriptable commands.
- Canonical dataclasses live in core/models.py and validate via core/validation.py.
- Database schema version is 2. Preserve version-1 migration, FTS index consistency, and future-version rejection.
- core/db.py owns transaction nesting and commit deferral. Do not add unconditional commit calls to helpers.
- core/sync.py validates bounded read-only sources, keeps local conflicts, and rolls back all writes on failure.
- Skill graphs require every dependency to exist and reject cycles. Use deterministic traversal without optional-library behavior changes.
- Database snapshots must use Database.backup(). Do not copy a live SQLite file or overwrite a running database.
- Data files and WAL/SHM sidecars are ignored. Never commit user state or generated databases.
- The current source corpus is example content. Do not claim it is medically reviewed, exhaustive, or field-ready.
- Tests live in remnant/tests and run under unittest without site packages. Test data must use temporary or in-memory databases.
