
# AGENTS.md — obsistant (Agent Instructions)

## What this repo is

**obsistant** is a Python **CLI tool** for automatically organizing and managing
Obsidian vaults. It focuses on:
- Organizing notes into vault subfolders based on tags and content type.
- Extracting hashtags from markdown and moving them into YAML frontmatter.
- Meeting note naming/formatting (YYMMDD_Title).
- Processing a “00-Quick Notes” inbox into the right vault locations.
- Backup/restore via `.bak`-like sidecar files.
- Optional markdown formatting via `mdformat` + `mdformat-gfm`.

Core design goal: **predictable bulk transformations on vaults** with safe dry-run,
clear reporting, and easy rollback.

## Expected vault conventions

obsistant assumes (or strongly favors) a vault layout like:

```
Your-Vault/
├── .obsistant/
│   ├── config.yaml        # Configuration file
│   └── storage/          # CrewAI memory storage
├── 00-Quick Notes/
├── 10-Meetings/
│   └── Archive/          # Archived meetings by year
├── 20-Notes/
│   ├── products/
│   ├── projects/
│   ├── devops/
│   ├── challenges/
│   ├── events/
│   └── various/
├── 30-Guides/
├── 40-Vacations/
└── 50-Files/
```

Agents must preserve these assumptions unless the user asks to change them.

## Repo structure

- `obsistant/` — Python package + CLI implementation
  - `cli.py` — Command line interface
  - `core/` — Core processing functions (frontmatter, tags, formatting, dates, file processing)
  - `vault/` — Vault-wide operations (processing orchestration, initialization)
  - `meetings/` — Meeting-specific operations (processing, archiving)
  - `notes/` — Notes organization (notes and quick notes processing)
  - `backup/` — Backup and restore operations
  - `config/` — Configuration management (schema, loading)
  - `agents/` — Future AI agents integration (placeholder)
- `tests/` — test suite
- `.github/workflows/` — CI
- `pyproject.toml` — packaging + tooling config
- `uv.lock` — locked deps
- `justfile` — task shortcuts
- `.pre-commit-config.yaml` — local checks & formatting hooks

When adding code:
- Core functions go in `obsistant/core/`
- Domain-specific operations go in respective modules (`vault/`, `meetings/`, `notes/`, `backup/`)
- Configuration logic stays in `obsistant/config/`
- CLI / orchestration stays in `obsistant/cli.py`
- Tests go in `tests/` mirroring module paths

## Tooling and dev commands

This project uses **uv** as its primary package manager.

### Install (dev)
```
uv sync --dev
```

### Run the CLI locally
```
uv run obsistant --help
uv run obsistant /path/to/vault
```

### Formatting extras
If touching formatting behavior, ensure the optional dependency path remains valid:
```
uv pip install -e '.[dev,formatting]'
# optional extra only:
uv pip install mdformat-gfm
```
obsistant must **gracefully skip** GFM formatting if `mdformat-gfm` is missing.

### Tests / lint
```
uv run pytest
uv run ruff check .
uv run ruff format .
```

### justfile shortcuts
Prefer `just <task>` when available. If unsure, open `justfile` first.

## CLI surface & invariants

Public commands:
- `init` — Initialize vault with structure and config.yaml
- `process` (default) — Process vault to extract tags and add metadata
- `meetings` — Organize meeting notes with standardized naming
- `notes` — Organize main notes by tags into subfolders
- `quick-notes` — Process quick notes and move to appropriate locations
- `backup` — Create vault backups
- `clear-backups` — Clear all backup files
- `restore` — Restore corrupted files from backups

Shared options:
- `--dry-run/-n`
- `--backup-ext`
- `--format/-f`
- `--verbose/-v`

## Transformation safety rules

1. Support dry-run (no writes).
2. Create backups before editing.
3. Keep operations idempotent.
4. Never lose user content.
5. Do not traverse outside vault.

## Parsing conventions

- Body hashtags → YAML frontmatter tags.
- Meeting notes use `YYMMDD_Title` pattern (configurable via config.yaml).

## Configuration

All hardcoded values have been moved to `config.yaml`:
- Vault folder names
- Target tags and ignored tags
- Tag regex pattern
- Meeting filename format and archive settings
- Backup extension
- Date formats and patterns
- Granola link pattern

Configuration priority:
1. CLI arguments (highest priority)
2. config.yaml (if present)
3. Defaults (if config.yaml doesn't exist)

The `init` command creates a vault with default config.yaml. All values can be customized.

## Agent workflow

1. Find similar existing logic.
2. Write a small plan.
3. Implement minimally.
4. Add tests.
5. Update README if CLI changes.

## Task playbooks

### Add a new rule
- Pure function in `obsistant/core/` → pipeline integration → fixture tests.

### Modify frontmatter/tagging
- Update functions in `obsistant/core/frontmatter.py` or `obsistant/core/tags.py`.
- Preserve unrelated metadata.
- Add round‑trip tests.

### Change formatting behavior
- Update `obsistant/core/formatting.py`.
- Test mdformat present/absent.

### Change backups
- Update `obsistant/backup/operations.py`.
- Preserve restore compatibility.

### Modify configuration
- Update `obsistant/config/schema.py` for new config options.
- Update `obsistant/vault/init.py` to include new defaults.
- Ensure backward compatibility or document breaking changes.

## Performance
- Avoid reading whole vaults.
- Pre‑compile regex.
- Keep algorithms O(n).

## Precedence
1. Existing code/tests
2. README
3. This AGENTS.md
