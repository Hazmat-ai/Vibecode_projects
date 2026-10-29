# Security and release scope

## Browser simulator

This app processes generated numbers and local settings. Adding authentication or a backend would add attack surface without protecting any existing shared resource. Settings are validated at import and control boundaries; arbitrary object keys, invalid cores, nonfinite numbers, invalid ranges, and excessive file sizes are rejected. The capture is bounded to 1,000 rows. CSV contains generated numeric values and controlled labels. Rendering escapes string content and uses only self-hosted scripts/styles under the included CSP.

The loopback preview server exposes only the simulator HTML and asset directory. It does not expose repository metadata, Python files, or databases. For public deployment, use a static host or the Nginx configuration; publish only the frontend files and use HTTPS at the edge. Pin a reviewed container image digest for a release. No production hosting is configured automatically.

## REMNANT

REMNANT is a local, offline CLI. Filesystem access is its trust boundary, not a user login system. Database files are permission-restricted where the OS supports it. Imports validate content types, sizes, identifier syntax, scores, control characters, and references. The supported YAML subset never instantiates Python objects; unknown YAML features are not promised to work. Do not treat the subset parser as a general YAML implementation.

Remote databases open in read-only/query-only mode, use a bounded query budget, require supported schema versions and ordinary required tables, and have size/row limits. Models and dependencies are checked before or within a single local transaction. Failed merges roll back article, skill, community, metadata, and conflict writes. Existing local records are retained; changes are recorded as conflicts. Communities union their known skills only when imported prerequisites are valid.

Database snapshots use Python's SQLite online backup interface, not raw copying of a live WAL database. The snapshot is completed in a private temporary file and published without replacing an existing destination. See [SQLite's backup documentation](https://sqlite.org/backup.html). A snapshot is safe to transport once complete; reopening a live folder is not equivalent to exporting a snapshot.

Encryption, physical access control, removable-media hygiene, and off-device retention remain operator responsibilities. The bundled articles are original example material, not medically or technically reviewed deployment content. Publishing an offline knowledge library requires an independent content review, source verification, accessibility review, and broader field testing.

## Release checks

- Run simulator engine tests, desktop/mobile browser flows, and stdlib-only Python tests.
- Check that a fresh seed works without installed site packages.
- Exercise backup/restore, conflict deduplication, corrupt inputs, late merge failure, and custom-record preservation.
- Verify exported CSV and settings files in the browser and test offline operation after loading.
- Inspect static-host headers and exposed paths in the actual hosting environment.

CI is supplied. Local tests do not certify the application's security, hardware timing, field reliability, medical content, or every operating system. There is no cloud API or AI provider to configure for these two applications.
