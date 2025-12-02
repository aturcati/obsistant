# Obsistant

obsistant is an opinionated automation layer for your Obsidian vault that combines **deterministic CLI tools** and **AI agents**.
It bulk-organizes notes, normalizes frontmatter, backs up and restores your vault, and runs agentic workflows (deep research, calendar summaries) — all while staying predictable, reversible, and scoped to your vault.

## Highlights

- **AI agents via CLI**: Run deep research or calendar/weekly-summary flows directly from the command line.
- **Deterministic processing**: Tag extraction, folder routing, meeting-note normalization, quick-notes triage.
- **Safety first**: Automatic backups, `--dry-run` previews, idempotent transforms, strict vault confinement.
- **RAG-ready**: Optional Qdrant integration for semantic search over your notes.

---

## Agentic workflows

obsistant ships with CrewAI-powered agent flows. Run them from the CLI:

### Deep Research (`research`)

Turn an open-ended question into a structured research note.

```bash
obsistant research /path/to/vault "How should I structure my Obsidian vault?"
```

- **Output**: `00-Quick Notes/YYYYMMDD_Shortened_Query.md` with `tags: [research]`.
- Requires `OPENAI_API_KEY` in `.obsistant/.env`.

### Calendar / Weekly Summary (`calendar`)

Fetch upcoming calendar events, enrich them, and write a weekly summary.

```bash
# First, authenticate with Google Calendar (one-time setup)
obsistant calendar-login /path/to/vault

# Then generate the weekly summary
obsistant calendar /path/to/vault
```

- **Output**: `10-Meetings/Weekly Summaries/Weekly_Events_Summary.md` with `tags: [weekly-summary, meeting]`.
- Requires Google OAuth credentials in `.obsistant/credentials.json` and `OPENAI_API_KEY` in `.obsistant/.env`.

### Environment setup for agents

Create `.obsistant/.env` in your vault:

```bash
OPENAI_API_KEY=your-openai-key
# For calendar integration
GOOGLE_API_KEY=...
```

Agent memory is stored in `.obsistant/storage/` (auto-created). You can customize work-event context by editing `.obsistant/storage/work/knowledge/user_preference.md`.

<details>
<summary><strong>Advanced: programmatic invocation</strong></summary>

```python
from pathlib import Path
from obsistant.agents.deep_research_flow.src.deep_research_flow import main as research
from obsistant.agents.calendar_flow.src.calendar_flow import main as calendar

vault = Path("/path/to/vault")

# Deep research
research.kickoff(vault_path=vault, user_query="Your question here")

# Calendar summary
calendar.kickoff(vault_path=vault, meetings_folder="10-Meetings")
```

</details>

---

## CLI commands

All commands share these options (where applicable):

| Option | Description |
|--------|-------------|
| `-n, --dry-run` | Preview changes without writing |
| `-b, --backup-ext` | Backup extension (default `.bak`) |
| `-f, --format` | Format markdown via `mdformat` |
| `-v, --verbose` | Verbose logging |

### `init` — Initialize a vault

```bash
obsistant init /path/to/vault
```

Creates the folder structure and `.obsistant/config.yaml`.

Options: `--overwrite-config`, `--skip-folders`.

### `process` — Main processing pass

```bash
obsistant process /path/to/vault
```

- Extracts `#tags` into frontmatter.
- Normalizes frontmatter fields (`created`, `modified`, `tags`, etc.).
- Applies tag-based routing rules.

### `meetings` — Organize meeting notes

```bash
obsistant meetings /path/to/vault
```

- Renames files to `YYMMDD_Title` format.
- Ensures `meeting` tag is present.
- Archives old meetings based on `archive_weeks`.

### `notes` — Organize notes by tags

```bash
obsistant notes /path/to/vault
```

Moves notes into `20-Notes/` subfolders based on their primary tag (e.g., `products/app` → `20-Notes/products/app/`).

### `quick-notes` — Triage quick-capture inbox

```bash
obsistant quick-notes /path/to/vault
```

- Routes `meeting`-tagged files to Meetings folder.
- Routes other tagged files to Notes subfolders.

### `backup` / `restore` / `clear-backups`

```bash
obsistant backup /path/to/vault --name "pre-migration"
obsistant restore /path/to/vault [--file specific.md]
obsistant clear-backups /path/to/vault
```

### `qdrant` — Vector database for RAG

```bash
obsistant qdrant start /path/to/vault   # Start Qdrant in Docker
obsistant qdrant stop /path/to/vault    # Stop Qdrant
obsistant qdrant ingest /path/to/vault  # Ingest notes into Qdrant
```

Ingest options: `--collection`, `--include-pdfs`, `--recreate-collection`, `--dry-run`.

Requires Docker and `OPENAI_API_KEY` in `.obsistant/.env`.

---

## The `.obsistant` folder

All configuration and agent state lives here:

```
Your-Vault/
├── .obsistant/
│   ├── config.yaml        # Main configuration
│   ├── .env               # API keys and secrets
│   ├── storage/           # CrewAI agent memory (auto-managed)
│   ├── qdrant_storage/    # Qdrant data (auto-managed)
│   ├── credentials.json   # Google OAuth credentials
│   └── token.json         # Google OAuth token
├── 00-Quick Notes/
├── 10-Meetings/
├── 20-Notes/
├── 30-Guides/
├── 40-Vacations/
└── 50-Files/
```

**Safe to edit**: `config.yaml`, `.env`, crew knowledge files under `storage/*/knowledge/`.

**Auto-managed**: `storage/`, `qdrant_storage/`, `credentials.json`, `token.json`.

You can delete `storage/` or `qdrant_storage/` to reset agent memory or the vector index.

### Configuration (`config.yaml`)

Priority: CLI args > `config.yaml` > built-in defaults.

```yaml
vault:
  folders:
    quick_notes: "00-Quick Notes"
    meetings: "10-Meetings"
    notes: "20-Notes"
    guides: "30-Guides"
    vacations: "40-Vacations"
    files: "50-Files"

tags:
  target_tags: [products, projects, devops, challenges, events]
  ignored_tags: [...]
  tag_regex: "(?<!\\w)#([\\w/-]+)(?=\\s|$)"

meetings:
  filename_format: "YYMMDD_Title"
  archive_weeks: 2
  auto_tag: "meeting"

processing:
  backup_ext: ".bak"
  date_formats: ["%Y-%m-%d", "%Y/%m/%d"]  # ... and more
  date_patterns: ["(\\d{4}[-/]\\d{1,2}[-/]\\d{1,2})"]  # ... and more

calendar:
  calendars: { primary: "primary" }
  credentials_path: ".obsistant/credentials.json"
  token_path: ".obsistant/token.json"
```

Omit any section to use defaults.

---

## Tags and frontmatter

- **Primary tags**: `products`, `projects`, `devops`, `challenges`, `events`.
- **Hierarchies**: `products/app` → `20-Notes/products/app/`.
- **Special tags**: `meeting` (meeting notes), `research` (research flow output).

Frontmatter field order: `created` → `modified` → `meeting-transcript` → `tags` → other fields.

Tag extraction uses regex `(?<!\w)#([\w/-]+)`, ignores code blocks and malformed tags, and de-duplicates with existing frontmatter tags.

---

## Safety

- **Dry runs**: `--dry-run` on all content-modifying commands.
- **Backups**: Files backed up with `.bak` extension before modification.
- **Idempotent**: Multiple runs converge to stable state.
- **Vault-scoped**: Operations never escape the vault root.

---

## Installation

```bash
# Using uv (recommended)
uv add obsistant
# or globally
uv tool install git+https://github.com/aturcati/obsistant.git

# Using pip
pip install obsistant

# From source
git clone https://github.com/aturcati/obsistant.git && cd obsistant && uv sync --dev
```

Optional extras: `mdformat-gfm` (table formatting), `pdfplumber` (PDF ingestion).

---

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run ruff format .
```

---

## Project structure

```
obsistant/
├── obsistant/
│   ├── cli.py       # CLI entrypoint
│   ├── core/        # Frontmatter, tags, dates, formatting
│   ├── vault/       # Vault orchestration and init
│   ├── meetings/    # Meeting processing
│   ├── notes/       # Notes organization
│   ├── backup/      # Backup/restore
│   ├── config/      # Config schema and loading
│   └── agents/      # CrewAI agent flows
├── tests/
├── AGENTS.md
└── pyproject.toml
```

---

## License

MIT — see `LICENSE`.

For issues, open a GitHub issue with OS, Python version, CLI logs (`--verbose`), and a minimal vault example if possible.
