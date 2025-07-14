# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-15

### Added
- Initial release of obsidian-formatter
- Core tag extraction functionality using regex pattern `(?<!\\w)#([\\w/-]+)`
- YAML frontmatter generation and merging
- Automatic file creation date insertion
- Markdown formatting support using mdformat
- Command-line interface with Click
- Backup file creation before processing
- Dry run mode for previewing changes
- Comprehensive test suite
- Support for nested tags (e.g., `#category/subcategory`)
- Support for hyphenated tags (e.g., `#long-tag-name`)
- Smart frontmatter merging without data loss
- UTF-8 encoding support
- Verbose logging options
- Error handling and user-friendly messages

### Features
- **Tag Extraction**: Extracts inline `#tags` from markdown content
- **Creation Date**: Adds file creation dates to frontmatter
- **Markdown Formatting**: Optional standardized markdown formatting
- **Safe Processing**: Creates backup files before making changes
- **Dry Run Mode**: Preview changes without modifying files
- **Smart Merging**: Non-destructively merges with existing frontmatter
- **Flexible Tag Support**: Supports various tag formats

### Technical Details
- Python 3.9+ compatibility
- Dependencies: PyYAML, Click, mdformat
- Cross-platform support (Windows, macOS, Linux)
- Comprehensive error handling
- File system safety measures
