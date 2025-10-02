# Obsistant

[![Tests](https://github.com/aturcati/obsistant/workflows/Tests/badge.svg)](https://github.com/yourusername/obsistant/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

I desperately needed a tool to optimize and automate my note taking and archiving system. I did not have time to properly code it. So I vibe-coded it.Use at your own risk!

A powerful Python CLI tool for automatically organizing and managing Obsidian vaults with intelligent tag extraction, file organization, and frontmatter management.

## Features

- **🏷️ Intelligent Tag Extraction**: Automatically extracts hashtags from markdown content and moves them to YAML frontmatter
- **📁 Smart File Organization**: Organizes notes into structured folders based on tags and content type
- **📅 Meeting Management**: Automatically formats meeting notes with standardized naming (YYMMDD_Title)
- **🔄 Quick Notes Processing**: Processes and organizes files from quick notes folder into appropriate locations
- **💾 Backup & Restore**: Comprehensive backup system with easy restoration capabilities
- **🚀 Batch Processing**: Process entire vaults or specific files with dry-run support
- **📊 Rich Reporting**: Detailed summaries and progress tracking with colored output
- **📝 Frontmatter Management**: Intelligent creation and modification date handling
- **🔗 Meeting Transcript Links**: Extracts meeting transcript URLs from "Chat with meeting transcript:" text
- **✨ Markdown Formatting**: Optional standardized markdown formatting using `mdformat`

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager. Install obsistant with:

```bash
uv add obsistant
```

Or install it globally:

```bash
uv tool install obsistant
```

### Using pip

```bash
pip install obsistant
```

### From Source

```bash
git clone https://github.com/yourusername/obsistant.git
cd obsistant
uv sync
```

### Development Installation

```bash
git clone https://github.com/yourusername/obsistant.git
cd obsistant
uv sync --dev
```

### Enhanced Formatting Installation

For improved GitHub Flavored Markdown (GFM) formatting support, install the formatting extras:

```bash
# Install with formatting dependencies
uv pip install -e '.[dev,formatting]'

# Or install just the formatting extras to an existing installation
uv pip install mdformat-gfm
```

This adds support for:
- GitHub Flavored Markdown table formatting
- Enhanced list and code block formatting
- Preserved table structure during formatting with `mdformat-gfm`
- Safeguard to skip formatting when `mdformat-gfm` is missing if tables are present
- Improved compatibility with GitHub markdown rendering

## Vault Structure

Obsistant is designed to work with a structured Obsidian vault. Here's the recommended organization:

```
Your-Vault/
├── 00-Quick Notes/          # Temporary notes for quick capture
├── 10-Meetings/            # Meeting notes with YYMMDD_Title format
├── 20-Notes/               # Main knowledge base, organized by tags
│   ├── products/           # Product-related notes
│   │   ├── product-a/
│   │   └── product-b/
│   ├── projects/           # Project documentation
│   │   ├── project-x/
│   │   └── project-y/
│   ├── devops/            # DevOps and infrastructure notes
│   │   └── tools/
│   ├── events/           # Event notes and conferences
│   └── various/          # Miscellaneous notes
├── 30-Guides/            # Documentation and guides
├── 40-Vacations/         # Personal time tracking
└── 50-Files/             # Attachments and resources
```

## Usage

### Basic Usage

```bash
obsistant /path/to/your/vault
```

### Available Commands

The tool supports multiple commands:

```bash
obsistant [OPTIONS] COMMAND [ARGS]...
```

**Commands:**
- `process`: Process Obsidian vault to extract tags and add metadata (default)
- `meetings`: Organize meeting notes with standardized naming
- `notes`: Organize main notes by tags into subfolders
- `quick-notes`: Process quick notes and move to appropriate locations
- `backup`: Create vault backups
- `clear-backups`: Clear all backup files for the specified vault
- `restore`: Restore corrupted files from backups

### Process Command

```bash
obsistant process [OPTIONS] VAULT_PATH
```

**Arguments:**
- `VAULT_PATH`: Path to your Obsidian vault directory

**Options:**
- `-n, --dry-run`: Show what would be done without making changes
- `-b, --backup-ext TEXT`: Backup file extension (default: `.bak`)
- `-f, --format`: Format markdown files for consistent styling (includes improved list formatting)
- `-v, --verbose`: Enable verbose output
- `--help`: Show help message and exit

### Clear Backups Command

```bash
obsistant clear-backups [OPTIONS] VAULT_PATH
```

Removes all backup files for the specified vault.

**Options:**
- `-v, --verbose`: Enable verbose output

### Restore Command

```bash
obsistant restore [OPTIONS] VAULT_PATH
```

Restore corrupted files from backups.

**Options:**
- `--file FILE`: Restore a specific file instead of all files
- `-v, --verbose`: Enable verbose output

### Universal Formatting Option

**All content-modifying commands** (`process`, `meetings`, `notes`, `quick-notes`) support the `-f / --format` option:

- **Consistent List Formatting**: Improved handling of bullet points and numbered lists with proper spacing and indentation
- **Standardized Headings**: Consistent heading formatting and spacing
- **Markdown Compliance**: Ensures all output follows markdown standards using `mdformat`
- **Link Formatting**: Proper formatting of markdown links and references
- **Code Block Formatting**: Consistent formatting of inline code and code blocks
- **Table Preservation**: GitHub Flavored Markdown tables are preserved and formatted correctly with `mdformat-gfm`

**Fallback Strategy:**

If the `mdformat-gfm` plugin is not available, the tool will detect pipe tables and skip formatting altogether to prevent corruption. This ensures the table structures in your markdown files remain intact, even if enhanced formatting is unavailable.

**Usage Examples:**
```bash
# Apply formatting to all commands
obsistant process ~/vault --format
obsistant meetings ~/vault --format
obsistant notes ~/vault --format
obsistant quick-notes ~/vault --format
```

### Specialized Commands

#### Organize Meeting Notes
```bash
obsistant meetings [OPTIONS] VAULT_PATH
```
- Renames files using YYMMDD_Title format
- Ensures all files have the 'meeting' tag
- Extracts dates from frontmatter or file creation date
- **Supports `-f / --format`** for consistent markdown formatting

#### Organize Main Notes by Tags
```bash
obsistant notes [OPTIONS] VAULT_PATH
```
- Moves files to appropriate subfolders based on tags
- Supports nested folder structures for subtags
- Handles these target tags: `products`, `projects`, `devops`, `challenges`, `events`
- **Supports `-f / --format`** for consistent markdown formatting

#### Process Quick Notes
```bash
obsistant quick-notes [OPTIONS] VAULT_PATH
```
- Processes files from Quick Notes folder
- Files with `meeting` tag → moved to Meetings folder
- Other files → moved to appropriate Notes subfolders
- Applies appropriate formatting based on destination
- **Supports `-f / --format`** for consistent markdown formatting

#### Create Vault Backup
```bash
obsistant backup [OPTIONS] VAULT_PATH
```
- Creates complete vault backup with timestamp
- Option to specify custom backup name
- Removes existing backup if same name exists

**Options:**
- `--name TEXT`: Custom backup name (default: timestamp)
- `-v, --verbose`: Enable verbose output

### Examples

#### Quick Start Examples
```bash
# Preview changes without modifying files
obsistant ~/Obsidian/Work --dry-run

# Process vault and apply changes
obsistant ~/Obsidian/Work
```

#### Basic Processing
```bash
# Process vault with default settings
obsistant ~/Documents/MyVault
```

#### Dry Run (Preview Changes)
```bash
# See what would be changed without making modifications
obsistant --dry-run ~/Documents/MyVault
```

#### With Formatting
```bash
# Process vault and format markdown for consistency
obsistant --format ~/Documents/MyVault
```

#### Custom Backup Extension
```bash
# Use custom backup file extension
obsistant --backup-ext .backup ~/Documents/MyVault
```

#### Verbose Output
```bash
# Enable detailed logging
obsistant --verbose ~/Documents/MyVault
```

#### Managing Backups
```bash
# Clear all backup files for a vault
obsistant clear-backups ~/Documents/MyVault

# Restore all files from backups
obsistant restore ~/Documents/MyVault

# Restore a specific file from backup
obsistant restore ~/Documents/MyVault --file ~/Documents/MyVault/note.md
```

#### Using New Command Structure
```bash
# Explicitly use the process command
obsistant process ~/Documents/MyVault --dry-run

# Process with formatting
obsistant process ~/Documents/MyVault --format
```

#### Specialized Commands Examples
```bash
# Process quick notes from daily capture
obsistant quick-notes ~/Documents/MyVault

# Organize meeting notes with formatting
obsistant meetings ~/Documents/MyVault --format

# Organize main notes by tags with formatting
obsistant notes ~/Documents/MyVault --format

# Process quick notes with improved formatting
obsistant quick-notes ~/Documents/MyVault --format

# Create backup before major changes
obsistant backup ~/Documents/MyVault --name "pre-migration"
```

#### Formatting Improvements Examples
```bash
# All these commands now support improved list formatting with -f/--format:

# Process vault with improved list and markdown formatting
obsistant process ~/vault --format

# Meeting notes with consistent bullet point formatting
obsistant meetings ~/vault --format

# Notes organization with standardized list formatting
obsistant notes ~/vault --format

# Quick notes processing with formatting improvements
obsistant quick-notes ~/vault --format
```

#### Daily Workflow
```bash
# 1. Process quick notes from daily capture
obsistant quick-notes ~/Documents/MyVault

# 2. Organize meeting notes
obsistant meetings ~/Documents/MyVault

# 3. Process and organize all notes
obsistant process ~/Documents/MyVault --dry-run  # Preview first
obsistant process ~/Documents/MyVault            # Apply changes
```

#### Migration Workflow
```bash
# 1. Create backup before major changes
obsistant backup ~/Documents/MyVault --name "pre-migration"

# 2. Process vault with dry run
obsistant process ~/Documents/MyVault --dry-run

# 3. Apply changes
obsistant process ~/Documents/MyVault

# 4. If issues occur, restore from backup
obsistant restore ~/Documents/MyVault
```

## Tag System

Obsistant uses a hierarchical tag system for organization:

### Primary Tags
- `products` - Product-related documentation
- `projects` - Project management and documentation
- `devops` - Infrastructure and deployment notes
- `challenges` - Technical challenges and solutions
- `events` - Conferences, meetings, and events

### Tag Hierarchy
Tags support nested structures using forward slashes:
- `products/awesome-app` → `20-Notes/products/awesome-app/`
- `projects/migration/phase1` → `20-Notes/projects/migration/phase1/`

### Special Tags
- `meeting` - Automatically applied to meeting notes

## Frontmatter Management

Obsistant automatically manages YAML frontmatter with these properties:

```yaml
---
created: '2024-01-15'        # Earliest date found (body content or file creation)
modified: '2024-01-16'       # File modification date (auto-updated)
meeting-transcript: 'url'    # Meeting transcript URL (if found)
tags:                        # Sorted alphabetically
  - products/awesome-app
  - devops/deployment
---
```

### Property Ordering
1. `created` - Creation date
2. `modified` - Last modification date
3. `meeting-transcript` - Meeting transcript URL (if present)
4. `tags` - Sorted tag list
5. Any other existing properties (preserved)

## Meeting Notes

Meeting notes are automatically formatted with:
- **Filename**: `YYMMDD_Title.md` (e.g., `240115_Project_Kickoff.md`)
- **Tags**: Automatically includes `meeting` tag
- **Date Extraction**: From frontmatter `created` field or file creation date

Example meeting note:
```markdown
---
created: '2024-01-15'
modified: '2024-01-15'
tags:
  - meeting
  - projects/awesome-app
---

# Project Kickoff Meeting

## Attendees
- John Doe
- Jane Smith

## Agenda
1. Project overview
2. Timeline discussion
3. Next steps
```

## Supported Date Formats

Obsistant automatically detects these date formats:
- ISO: `2024-01-15`, `2024/01/15`
- US: `01/15/2024`, `1/15/2024`
- European: `15/01/2024`, `15.01.2024`
- Long: `January 15, 2024`, `Jan 15, 2024`

## How It Works

### Tag Extraction

The tool uses the regex pattern `(?<!\\w)#([\\w/-]+)` to find tags in your markdown content:

**Before:**
```markdown
# My Note

This is a note about #python programming with #web-development.
I'm working on a #project/backend task.
```

**After:**
```markdown
---
created: '2024-01-15'
tags:
- project/backend
- python
- web-development
---
# My Note

This is a note about #python programming with #web-development.
I'm working on a #project/backend task.
```

### Smart Frontmatter Merging

The tool intelligently merges with existing frontmatter:

**Before:**
```markdown
---
title: My Important Note
author: John Doe
tags:
- existing-tag
---

# Content

Date: 2024-01-10

This has a #new-tag in it.
```

**After:**
```markdown
---
author: John Doe
created: '2024-01-10'
modified: '2024-01-15'
tags:
- existing-tag
- new-tag
title: My Important Note
---

# Content

This has a  in it.
```

### Supported Tag Formats

- Simple tags: `#tag`
- Nested tags: `#category/subcategory`
- Hyphenated tags: `#long-tag-name`
- Mixed formats: `#project/web-development`

### What Gets Ignored

- Tags within words (e.g., `email@domain.com#hashtag`)
- Tags in code blocks
- Malformed tags

## Behavior & Safety

### Backup Strategy

The tool prioritizes file safety through a comprehensive backup strategy:

- **Automatic Backups**: Before modifying any file, creates a backup with `.bak` extension (configurable via `--backup-ext`)
- **Backup Location**: Backups are created in the same directory as the original file
- **Backup Retention**: Existing backups are overwritten on subsequent runs
- **Restoration**: Simply remove the extension to restore from backup (e.g., `note.md.bak` → `note.md`)

### Merge Rules

The tool follows intelligent merge rules when processing frontmatter:

#### Tag Merging
- **Preservation**: Existing tags in frontmatter are preserved
- **Deduplication**: Duplicate tags are automatically removed
- **Alphabetical Sorting**: Final tag list is sorted alphabetically
- **Format Consistency**: All tags are converted to lowercase with consistent formatting

#### Creation Date Handling
- **Non-destructive**: Only adds `created` field if it doesn't already exist
- **Earliest Date**: Uses the earliest date found between body content and file metadata
- **Body Date Extraction**: Recognizes various date formats in the first 10 lines of content
- **Format**: ISO date format (YYYY-MM-DD) enclosed in quotes

#### Modification Date Handling
- **Always Updated**: `modified` field is always updated with current file modification time
- **Source**: Uses file system modification time
- **Format**: ISO date format (YYYY-MM-DD) enclosed in quotes

#### Frontmatter Structure
- **Field Ordering**: Properties are ordered as: `created`, `modified`, `meeting-transcript`, `tags`, then other existing fields
- **Existing Fields**: All existing frontmatter fields are preserved
- **YAML Compliance**: Ensures valid YAML syntax throughout

### Safety Features

- **Dry Run Mode**: Preview all changes with `--dry-run` before applying
- **UTF-8 Encoding**: Properly handles Unicode characters and international text
- **Error Handling**: Graceful error handling with informative messages
- **Validation**: Validates YAML syntax before writing files
- **Atomic Operations**: Files are processed atomically to prevent corruption

## Development

### Setup Development Environment

```bash
git clone https://github.com/aturcati/obsistant.git
cd obsistant
uv sync --dev
```

## Project Structure

```
obsistant/
├── obsistant/
│   ├── __init__.py
│   ├── cli.py          # Command line interface
│   └── processor.py    # Core processing logic
├── tests/
│   └── test_processor.py
├── pyproject.toml      # Project configuration
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## Requirements

- Python 3.9+
- PyYAML >= 6.0
- Click >= 8.1
- mdformat >= 0.7.22

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/aturcati/obsistant/issues) page
2. Create a new issue if your problem isn't already listed
3. Provide detailed information about your setup and the issue

## Acknowledgments

- [Obsidian](https://obsidian.md/) for creating an amazing knowledge management tool
- [mdformat](https://github.com/executablebooks/mdformat) for markdown formatting capabilities
- [Click](https://click.palletsprojects.com/) for the excellent CLI framework
