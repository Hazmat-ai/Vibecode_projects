# REMNANT

An offline Python knowledge library and community skill planner. Source has been unpacked from `APP2.zip` into a normal reviewable project. No database file or mandatory third-party dependency is shipped.

## Start

From the repository root:

```sh
python3 remnant-project/remnant/scripts/seed_db.py
python3 remnant-project/remnant/main.py --ui plain
```

Use a current supported Python version. The source retains Python 3.8-compatible syntax. The initial seed contains **3 example articles and 6 skills**; this is not a complete or reviewed survival reference.

The database defaults to `remnant-project/remnant/data/remnant.db`. Pass `--db PATH` **before** the main command to select another database. This path is private local state, never a static-host asset.

## Commands

```sh
python3 remnant-project/remnant/main.py library search "water"
python3 remnant-project/remnant/main.py library top --limit 10 --domain food
python3 remnant-project/remnant/main.py library read water-purification-boiling
python3 remnant-project/remnant/main.py community new "Milton Lab"
python3 remnant-project/remnant/main.py tree next --community milton-lab
python3 remnant-project/remnant/main.py tree learn --community milton-lab --skill fire-making
python3 remnant-project/remnant/main.py tree path --community milton-lab --skill water-purification
python3 remnant-project/remnant/main.py library export water-purification-boiling --format md --output water.md
```

Learning requires existing, learned prerequisites. Unlearning a prerequisite is blocked while a known dependent still needs it. Graphs reject cycles and missing nodes. Traversal is deterministic, and shared branches are rendered once with references to avoid exponential output.

`--ui tui` is retained as a compatibility option for optional formatted terminal output. It gracefully falls back to plain output when optional dependencies are unavailable; it is not a separate full-screen application. The default plain UI and all core functions work with the standard library alone.

## Imports and data contracts

```sh
python3 remnant-project/remnant/main.py library add --file article.yaml
python3 remnant-project/remnant/scripts/seed_db.py --update
```

The supported YAML subset includes flat mappings, scalar/list values, and literal/folded text blocks as used in `data/seed/`. It has a 250 KB text limit, rejects duplicate mapping keys, and preserves quoted scalar strings. Full YAML anchors, arbitrary tags, and complex nested YAML schemas are not supported. Models validate IDs, domains, numeric ranges, lists, dates, and terminal control characters.

IDs are lowercase words separated by hyphens. Scores are 0–100, difficulty 1–5, and required/unlocked skills are lists of IDs. Article requirements are references; skill requirements form a directed acyclic graph. `unlocks` is descriptive source metadata; traversal is derived from `requires`.

Seed updates use a single transaction and preserve locally added custom records. Schema version 2 replaces the old FTS triggers with correct external-content index updates and rebuilds old version-1 indexes. Future unknown schema versions are rejected. Back up a database before upgrading and avoid downgrading it to the older archive code.

## Snapshots and USB merge

```sh
python3 remnant-project/remnant/main.py sync export --output remnant-snapshot.db
python3 remnant-project/remnant/main.py sync merge --source /path/to/other-snapshot.db
```

Export uses SQLite's online backup API, includes committed WAL changes, and refuses to overwrite an existing path. Choose a new filename for each snapshot. To restore, close all REMNANT processes, preserve the current database folder, place a validated snapshot at your chosen database path, and ensure stale WAL/SHM sidecars from the old database are not reused. Verify restoration with search and `tree show` before continuing work.

Merge is additive: new records are imported, differing existing records are retained locally and recorded in `sync_conflicts`, and community knowledge is unioned. Repeated identical conflicts are not duplicated. A late validation or database failure rolls back the entire merge. Sources must already exist and be smaller than 64 MiB, with no more than 10,000 records per required table. Sources are opened read-only; a misspelled source path never creates a new database.

Conflict records are available through `Database.list_conflicts()` for operator review. A full conflict-resolution interface is not implemented. Choose reviewed local corrections explicitly rather than assuming sync resolves conflicting knowledge for you.

## Tests

```sh
python3 -S -m unittest discover -s remnant-project/remnant/tests -v
```

Tests cover FTS updates/deletion, imports, dependencies, learning/unlearning, seed preservation, offline CLI execution, backups/restoration, malformed sources, conflict deduplication, community union, and atomic rollback. All tests use temporary databases or in-memory state.
