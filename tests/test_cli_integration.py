"""Integration tests for CLI commands with mini vaults and format functionality."""

import tempfile
from pathlib import Path

import click.testing

from obsistant.cli import cli


class TestCLIIntegration:
    """Test CLI integration with mini vaults and format functionality."""

    def test_process_format_dry_run_single_tag_file(self) -> None:
        """Test process command with --format --dry-run on file with single tag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create mini vault structure
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create a test file with single tag (no front-matter)
            test_file = vault_path / "test_single_tag.md"
            original_content = """# Sample without front-matter and a single tag
This is a markdown file without front-matter.

#tag1
"""
            test_file.write_text(original_content)

            # Run the CLI command with format and dry-run
            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--format", "--dry-run"]
            )

            # Check command succeeded
            assert result.exit_code == 0
            assert "Total files processed: 0" in result.output
            assert "+1 tags" in result.output

            # Verify original file is unchanged (dry-run)
            assert test_file.read_text() == original_content

    def test_process_format_dry_run_multiple_tags_file(self) -> None:
        """Test process command with --format --dry-run on file with multiple tags."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create a test file with existing front-matter and multiple tags
            test_file = vault_path / "test_multiple_tags.md"
            original_content = """---
title: "Sample with existing front-matter"
author: "Test Author"
---

# Sample with existing front-matter and multiple tags
This is a markdown file with existing front-matter.

#tag1 #tag2 #tag3

Some content here.
"""
            test_file.write_text(original_content)

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--format", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Total files processed: 0" in result.output
            assert "+3 tags" in result.output

            # Verify original file is unchanged
            assert test_file.read_text() == original_content

    def test_process_format_dry_run_edge_cases_file(self) -> None:
        """Test process command with --format --dry-run on file with edge cases."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create a test file with edge cases (comments, code blocks)
            test_file = vault_path / "test_edge_cases.md"
            original_content = """# Sample with edge cases
This file contains edge cases.

<!-- This is a comment with #fake-tag -->

```python
# This is a code block with #fake-tag
def hello():
    print("Hello #world")
```

Real tags: #real-tag1 #real-tag2

More content with a `#code-tag` in inline code.

#final-tag
"""
            test_file.write_text(original_content)

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--format", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Total files processed: 0" in result.output
            assert "+3 tags" in result.output

            # Verify original file is unchanged
            assert test_file.read_text() == original_content

    def test_process_format_dry_run_list_formatting(self) -> None:
        """Test process command with --format --dry-run on file with bullet points."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create a test file with nested bullet points that need formatting
            test_file = vault_path / "test_bullet_lists.md"
            original_content = """# Bullet List Test

- Main OTC limitations:

    - Poor documentation quality

    - Missing critical services (e.g., secrets manager, proper IAM)

    - Limited service sophistication compared to hyperscalers

    - Requires workarounds that increase development time

#test-tag
"""
            test_file.write_text(original_content)

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--format", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Total files processed: 0" in result.output
            assert "+1 tags" in result.output

            # Verify original file is unchanged (dry-run)
            assert test_file.read_text() == original_content

    def test_process_format_dry_run_mixed_list_types(self) -> None:
        """Test process command with --format --dry-run on file with mixed list types."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create a test file with mixed bullet and ordered lists
            test_file = vault_path / "test_mixed_lists.md"
            original_content = """# Mixed List Types

- Unordered list item

    1. Ordered sub-item

    2. Another ordered sub-item

        - Nested unordered item

        - Another nested unordered item

- Another main unordered item

    1. First ordered sub-item

    2. Second ordered sub-item

#organization #formatting
"""
            test_file.write_text(original_content)

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--format", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Total files processed: 0" in result.output
            assert "+2 tags" in result.output

            # Verify original file is unchanged
            assert test_file.read_text() == original_content

    def test_meetings_format_dry_run(self) -> None:
        """Test meetings command with --format --dry-run."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create meetings folder
            meetings_folder = vault_path / "10-Meetings"
            meetings_folder.mkdir()

            # Create a meeting file with formatting issues
            meeting_file = meetings_folder / "meeting_notes.md"
            original_content = """---
title: "Team Meeting"
---

# Team Meeting Notes

- Action items:

    - Review the proposal

    - Update documentation

    - Schedule follow-up

#meeting #team-sync
"""
            meeting_file.write_text(original_content)

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["meetings", str(vault_path), "--format", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Meetings Folder Processing Summary" in result.output
            assert "+2 tags" in result.output

            # Verify original file is unchanged
            assert meeting_file.read_text() == original_content

    def test_notes_format_dry_run(self) -> None:
        """Test notes command with --format --dry-run."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create notes folder
            notes_folder = vault_path / "20-Notes"
            notes_folder.mkdir()

            # Create a note file
            note_file = notes_folder / "project_notes.md"
            original_content = """# Project Notes

Some notes about the project.

- Key requirements:

    - Scalability

    - Security

        - Authentication

        - Authorization

    - Performance

#projects #development
"""
            note_file.write_text(original_content)

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["notes", str(vault_path), "--format", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Notes Folder Processing Summary" in result.output
            assert "+2 tags" in result.output

            # Verify original file is unchanged
            assert note_file.read_text() == original_content

    def test_quick_notes_format_dry_run(self) -> None:
        """Test quick-notes command with --format --dry-run."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create required folders for quick-notes command
            quick_notes_folder = vault_path / "00-Quick Notes"
            notes_folder = vault_path / "20-Notes"
            quick_notes_folder.mkdir()
            notes_folder.mkdir()

            # Create a quick note file
            note_file = quick_notes_folder / "quick_note.md"
            original_content = """# Quick Note

This is a quick note with some formatting issues.

- Todo:

    - Task 1

    - Task 2

        - Subtask A

        - Subtask B

#productivity #quick-capture
"""
            note_file.write_text(original_content)

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["quick-notes", str(vault_path), "--format", "--dry-run"]
            )

            assert result.exit_code == 0
            # For quick-notes, we just check it runs successfully
            # The output format may vary depending on what it finds to process
            assert "Quick Notes Processing Summary" in result.output
            assert "+2 tags" in result.output

            # Verify original file is unchanged
            assert note_file.read_text() == original_content

    def test_process_format_dry_run_specific_file(self) -> None:
        """Test process command with --format --dry-run on specific file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create multiple files but only process one
            test_file1 = vault_path / "test1.md"
            test_file2 = vault_path / "test2.md"

            content1 = """# Test File 1

- List item 1

    - Nested item

- List item 2

#file1
"""
            content2 = """# Test File 2

Some other content.

#file2
"""
            test_file1.write_text(content1)
            test_file2.write_text(content2)

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli,
                [
                    "process",
                    str(vault_path),
                    "--file",
                    str(test_file1),
                    "--format",
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0
            assert "File Processing Summary" in result.output
            assert "Total tags added: 1" in result.output

            # Verify both files are unchanged (dry-run)
            assert test_file1.read_text() == content1
            assert test_file2.read_text() == content2

    def test_process_format_dry_run_empty_vault(self) -> None:
        """Test process command with --format --dry-run on empty vault."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--format", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Total files processed: 0" in result.output

    def test_process_format_dry_run_vault_with_subdirectories(self) -> None:
        """Test process command with --format --dry-run on vault with subdirectories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Create subdirectories with files
            subdir1 = vault_path / "folder1"
            subdir2 = vault_path / "folder2"
            subdir1.mkdir()
            subdir2.mkdir()

            # Create files in subdirectories
            file1 = subdir1 / "note1.md"
            file2 = subdir2 / "note2.md"

            content1 = """# Note in Folder 1

- Item A

    - Sub-item 1

    - Sub-item 2

#folder1
"""
            content2 = """# Note in Folder 2

Some content here.

#folder2
"""

            file1.write_text(content1)
            file2.write_text(content2)

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--format", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "Total files processed: 0" in result.output
            assert "Total tags added: 2" in result.output

            # Verify both files are unchanged
            assert file1.read_text() == content1
            assert file2.read_text() == content2

    def test_process_format_dry_run_without_format_flag(self) -> None:
        """Test process command with --dry-run but without --format flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            test_file = vault_path / "test.md"
            original_content = """# Test

- Badly formatted list:

    - Item 1

    - Item 2

#test
"""
            test_file.write_text(original_content)

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["process", str(vault_path), "--dry-run"])

            assert result.exit_code == 0
            assert "Total files processed: 0" in result.output
            assert "Total tags added: 1" in result.output
            # This test verifies that format flag was not used
            assert "format markdown" not in result.output.lower()

            # Verify file is unchanged
            assert test_file.read_text() == original_content
