# Vibecode Projects development context

This repository contains two independent applications. Read README.md and the relevant project documentation before editing.

## Signal Bench

- Entry point: simulator.html; styles and browser controller live under simulator/.
- Pure model: simulator/engine.js, shared by browser and Node tests.
- Preserve explicit distinctions between instructions, modeled cycles, measured hardware results, and CPU utilization.
- Do not reintroduce fabricated RTOS, memory, power, or efficiency comparisons.
- Keep clocks labeled as example system settings, with documented exception-entry assumptions.
- Keep browser assets self-hosted, settings validated, captures bounded, and user text escaped.
- The Python preview server is loopback-only and must not serve repository/database files.

## REMNANT

- Source: remnant-project/remnant; source no longer lives inside APP2.zip.
- Offline terminal application; no authentication, network service, LLM integration, or mandatory third-party package.
- Validate models at every import/persistence boundary.
- Merges open sources read-only and use one atomic local transaction; helpers must defer commits inside it.
- Preserve custom records during seeding and existing local content during conflict merges.
- Use SQLite online backup, never raw copying of a live WAL database.
- Reject missing dependencies and cycles, and preserve prerequisites in learned community state.
- Keep Python 3.8-compatible syntax and stdlib-only tests. Prefer current supported Python for actual deployment.

Run npm test, npm run test:python, npm run test:e2e, formatting checks, and audit before release. Demo recordings must show actual application interactions and identify simulated rather than hardware data. Publication must preserve new remote work; never force-update main to an older base.
