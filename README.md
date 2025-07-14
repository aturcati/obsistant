# Obsidian Formatter

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful CLI tool for processing Obsidian vaults to extract inline `#tags` from markdown content and add them to YAML frontmatter, along with automatic file creation date insertion and optional markdown formatting.

## Features

- **Tag Extraction**: Automatically extracts inline `#tags` from markdown content and adds them to YAML frontmatter
- **Creation Date**: Adds file creation dates to frontmatter if not already present
- **Markdown Formatting**: Optional standardized markdown formatting using `mdformat`
- **Safe Processing**: Creates backup files before making any changes
- **Dry Run Mode**: Preview changes without modifying files
- **Smart Merging**: Non-destructively merges with existing frontmatter
- **Flexible Tag Support**: Supports nested tags like `#category/subcategory` and hyphenated tags like `#long-tag-name`

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager. Install obsidian-formatter with:

```bash
uv add obsidian-formatter
```

Or install it globally:

```bash
uv tool install obsidian-formatter
```

### Using pip

```bash
pip install obsidian-formatter
```

### From Source

```bash
git clone https://github.com/yourusername/obsidian-formatter.git
cd obsidian-formatter
uv sync
```

### Development Installation

```bash
git clone https://github.com/yourusername/obsidian-formatter.git
cd obsidian-formatter
uv sync --dev
```

## Usage

### Basic Usage

```bash
obsidian-formatter /path/to/your/vault
```

### Command Line Options

```bash
obsidian-formatter [OPTIONS] VAULT_PATH
```

**Arguments:**
- `VAULT_PATH`: Path to your Obsidian vault directory

**Options:**
- `-n, --dry-run`: Show what would be done without making changes
- `-b, --backup-ext TEXT`: Backup file extension (default: `.bak`)
- `-f, --format`: Format markdown files for consistent styling
- `-v, --verbose`: Enable verbose output
- `--help`: Show help message and exit

### Examples

#### Quick Start Examples
```bash
# Preview changes without modifying files
obsidian-formatter ~/Obsidian/Work --dry-run

# Process vault and apply changes
obsidian-formatter ~/Obsidian/Work
```

#### Basic Processing
```bash
# Process vault with default settings
obsidian-formatter ~/Documents/MyVault
```

#### Dry Run (Preview Changes)
```bash
# See what would be changed without making modifications
obsidian-formatter --dry-run ~/Documents/MyVault
```

#### With Formatting
```bash
# Process vault and format markdown for consistency
obsidian-formatter --format ~/Documents/MyVault
```

#### Custom Backup Extension
```bash
# Use custom backup file extension
obsidian-formatter --backup-ext .backup ~/Documents/MyVault
```

#### Verbose Output
```bash
# Enable detailed logging
obsidian-formatter --verbose ~/Documents/MyVault
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

This has a #new-tag in it.
```

**After:**
```markdown
---
author: John Doe
created: '2024-01-15'
tags:
- existing-tag
- new-tag
title: My Important Note
---

# Content

This has a #new-tag in it.
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
- **Source Priority**: Uses file system creation time when available
- **Format**: ISO date format (YYYY-MM-DD) enclosed in quotes

#### Frontmatter Structure
- **Field Ordering**: Fields are sorted alphabetically for consistency
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
git clone https://github.com/yourusername/obsidian-formatter.git
cd obsidian-formatter
uv sync --dev
```

### Running Tests

```bash
uv run pytest
```

### Running Tests with Coverage

```bash
uv run pytest --cov=obsidian_formatter
```

### Code Style

The project uses standard Python formatting. You can format code using:

```bash
uv run black obsidian_formatter/
```

## Project Structure

```
obsidian-formatter/
├── obsidian_formatter/
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

We welcome contributions to obsidian-formatter! Here's how to get started:

### Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/obsidian-formatter.git
   cd obsidian-formatter
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
uv run pytest --cov=obsidian_formatter

# Format code
uv run black obsidian_formatter/

# Check code style
uv run black --check obsidian_formatter/

# Run linting (if configured)
uv run ruff check obsidian_formatter/
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

- Check existing [Issues](https://github.com/yourusername/obsidian-formatter/issues) and [Pull Requests](https://github.com/yourusername/obsidian-formatter/pulls)
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

1. Check the [Issues](https://github.com/yourusername/obsidian-formatter/issues) page
2. Create a new issue if your problem isn't already listed
3. Provide detailed information about your setup and the issue

## Acknowledgments

- [Obsidian](https://obsidian.md/) for creating an amazing knowledge management tool
- [mdformat](https://github.com/executablebooks/mdformat) for markdown formatting capabilities
- [Click](https://click.palletsprojects.com/) for the excellent CLI framework
