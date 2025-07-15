# Obsistant

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful CLI tool for processing Obsidian vaults to extract inline `#tags` from markdown content and add them to YAML frontmatter, along with automatic creation and modification date insertion and optional markdown formatting.

## Features

- **Tag Extraction**: Automatically extracts inline `#tags` from markdown content and adds them to YAML frontmatter
- **Creation Date**: Adds creation dates using the earliest date between body content and file metadata
- **Modification Date**: Adds file modification dates to frontmatter
- **Meeting Transcript Links**: Extracts meeting transcript URLs from "Chat with meeting transcript:" text
- **Markdown Formatting**: Optional standardized markdown formatting using `mdformat`
- **Safe Processing**: Creates backup files before making any changes
- **Dry Run Mode**: Preview changes without modifying files
- **Smart Merging**: Non-destructively merges with existing frontmatter
- **Flexible Tag Support**: Supports nested tags like `#category/subcategory` and hyphenated tags like `#long-tag-name`

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
- `-f, --format`: Format markdown files for consistent styling
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
git clone https://github.com/yourusername/obsistant.git
cd obsistant
uv sync --dev
```

### Running Tests

```bash
uv run pytest
```

### Running Tests with Coverage

```bash
uv run pytest --cov=obsistant
```

### Code Style

The project uses standard Python formatting. You can format code using:

```bash
uv run black obsistant/
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

## Contributing

We welcome contributions to obsistant! Here's how to get started:

### Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/obsistant.git
   cd obsistant
   ```
3. **Set up development environment**:
   ```bash
   uv sync --dev
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
5. **Make your changes** and add tests if applicable
6. **Run tests** to ensure everything works:
   ```bash
   uv run pytest
   ```
7. **Commit your changes**:
   ```bash
   git commit -m 'Add some amazing feature'
   ```
8. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```
9. **Open a Pull Request** on GitHub

### Development Guidelines

#### Code Style
- Use [Black](https://black.readthedocs.io/) for code formatting
- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use type hints where appropriate
- Keep line length to 88 characters (Black default)

#### Testing
- Write tests for new functionality
- Ensure all tests pass before submitting
- Aim for good test coverage
- Use descriptive test names

#### Documentation
- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update CLI help text if adding new options
- Consider adding usage examples

#### Pull Request Guidelines
- **Title**: Use a clear, descriptive title
- **Description**: Explain what changes were made and why
- **Testing**: Describe how you tested the changes
- **Breaking Changes**: Clearly document any breaking changes
- **Issue Reference**: Link to relevant issues if applicable

### Types of Contributions

#### Bug Fixes
- Report bugs via GitHub Issues
- Include steps to reproduce
- Provide system information (OS, Python version)
- Submit fixes with tests when possible

#### Feature Requests
- Discuss new features in GitHub Issues first
- Explain the use case and benefits
- Consider backwards compatibility
- Provide implementation details if possible

#### Documentation
- Fix typos and improve clarity
- Add examples and usage scenarios
- Update outdated information
- Translate documentation (if applicable)

### Development Commands

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=obsistant

# Format code
uv run black obsistant/

# Check code style
uv run black --check obsistant/

# Run linting (if configured)
uv run ruff check obsistant/
```

### Commit Message Guidelines

Use conventional commit format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for test additions/changes
- `chore:` for maintenance tasks

Examples:
```
feat: add support for nested tag extraction
fix: handle edge case in frontmatter parsing
docs: update installation instructions
```

### Getting Help

- Check existing [Issues](https://github.com/yourusername/obsistant/issues) and [Pull Requests](https://github.com/yourusername/obsistant/pulls)
- Ask questions in GitHub Discussions (if enabled)
- Read the existing code and tests for examples
- Join the community chat (if available)

### Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/obsistant/issues) page
2. Create a new issue if your problem isn't already listed
3. Provide detailed information about your setup and the issue

## Acknowledgments

- [Obsidian](https://obsidian.md/) for creating an amazing knowledge management tool
- [mdformat](https://github.com/executablebooks/mdformat) for markdown formatting capabilities
- [Click](https://click.palletsprojects.com/) for the excellent CLI framework
