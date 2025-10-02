"""Tests for the processor module."""

import os
from datetime import datetime
from pathlib import Path

from obsistant.processor import (
    _find_target_folder_for_tags,
    _generate_meeting_filename,
    _move_file_to_folder,
    clear_backups,
    create_backup_path,
    create_vault_backup,
    extract_date_from_body,
    extract_granola_link,
    extract_tags,
    format_markdown,
    get_file_creation_date,
    merge_frontmatter,
    parse_date_string,
    process_file,
    process_vault,
    render_frontmatter,
    restore_files,
    split_frontmatter,
    walk_markdown_files,
)


def read_fixture(filename: str) -> str:
    """Helper function to read fixture files."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(fixture_path, encoding="utf-8") as f:
        return f.read()


class TestExtractTags:
    """Test tag extraction functionality."""

    def test_extract_single_tag(self) -> None:
        text = "This is a #test document"
        tags, body = extract_tags(text)
        assert tags == {"test"}
        assert body == "This is a  document"

    def test_extract_multiple_tags(self) -> None:
        text = "This has #tag1 and #tag2 and #tag3"
        tags, body = extract_tags(text)
        assert tags == {"tag1", "tag2", "tag3"}

    def test_extract_nested_tags(self) -> None:
        text = "This has #category/subcategory and #project/task"
        tags, body = extract_tags(text)
        assert tags == {"category/subcategory", "project/task"}

    def test_extract_tags_with_hyphens(self) -> None:
        text = "This has #long-tag-name and #another-tag"
        tags, body = extract_tags(text)
        assert tags == {"long-tag-name", "another-tag"}

    def test_no_tags(self) -> None:
        text = "This has no tags"
        tags, body = extract_tags(text)
        assert tags == set()

    def test_ignore_hashtags_in_words(self) -> None:
        text = "email@domain.com#hashtag should not be extracted"
        tags, body = extract_tags(text)
        assert tags == set()

    def test_ignore_hashtags_in_inline_code(self) -> None:
        text = "This has a `#code-tag` in inline code and #real-tag outside"
        tags, body = extract_tags(text)
        assert tags == {"real-tag"}
        assert "code-tag" not in tags

    def test_ignore_hashtags_in_code_blocks(self) -> None:
        text = """This is normal text with #normal-tag

```python
def function():
    # This is a comment with #code-tag
    print("Hello #world")
```

More text with #another-tag"""
        tags, body = extract_tags(text)
        assert tags == {"normal-tag", "another-tag"}
        assert "code-tag" not in tags
        assert "world" not in tags

    def test_ignore_hashtags_in_html_comments(self) -> None:
        text = """This has #real-tag1 in normal text

<!-- This is a comment with #fake-tag -->

And #real-tag2 after comment"""
        tags, body = extract_tags(text)
        assert tags == {"real-tag1", "real-tag2"}
        assert "fake-tag" not in tags

    def test_ignore_hashtags_in_markdown_links(self) -> None:
        text = (
            "Check out [this link with #tag-in-link](https://example.com) and #real-tag"
        )
        tags, body = extract_tags(text)
        assert tags == {"real-tag"}
        assert "tag-in-link" not in tags

    def test_ignore_hashtags_in_quoted_strings(self) -> None:
        text = 'This has #real-tag and "quoted text with #quoted-tag" here'
        tags, body = extract_tags(text)
        assert tags == {"real-tag"}
        assert "quoted-tag" not in tags

    def test_ignore_hashtags_in_longer_strings(self) -> None:
        text = "This string contains #Pv2$n56k48dypEY and should not extract tags."
        tags, body = extract_tags(text)
        assert tags == set()  # Hash in longer string should be ignored
        assert body == text


class TestSplitFrontmatter:
    """Test frontmatter splitting functionality."""

    def test_split_with_frontmatter(self) -> None:
        text = """---
title: Test
author: John
---

# Content

Some content here."""
        frontmatter, body = split_frontmatter(text)
        assert frontmatter == {"title": "Test", "author": "John"}
        assert body == "\n\n# Content\n\nSome content here."

    def test_split_without_frontmatter(self) -> None:
        text = "# Content\n\nSome content here."
        frontmatter, body = split_frontmatter(text)
        assert frontmatter is None
        assert body == text

    def test_split_invalid_yaml(self) -> None:
        text = """---
title: Test
  invalid: yaml: structure
---

# Content"""
        frontmatter, body = split_frontmatter(text)
        assert frontmatter is None
        assert body == text


class TestMergeFrontmatter:
    """Test frontmatter merging functionality."""

    def test_merge_with_no_existing_frontmatter(self) -> None:
        result = merge_frontmatter(None, {"tag1", "tag2"})
        assert result == {"tags": ["tag1", "tag2"]}

    def test_merge_with_existing_frontmatter(self) -> None:
        existing = {"title": "Test", "tags": ["existing"]}
        result = merge_frontmatter(existing, {"new-tag"})
        assert result == {"title": "Test", "tags": ["existing", "new-tag"]}

    def test_merge_duplicate_tags(self) -> None:
        existing = {"tags": ["tag1", "tag2"]}
        result = merge_frontmatter(existing, {"tag1", "tag3"})
        assert result == {"tags": ["tag1", "tag2", "tag3"]}

    def test_merge_empty_tags(self) -> None:
        existing = {"title": "Test"}
        result = merge_frontmatter(existing, set())
        assert result == {"title": "Test"}
        assert "tags" not in result


class TestRenderFrontmatter:
    """Test frontmatter rendering functionality."""

    def test_render_simple_frontmatter(self) -> None:
        data = {"title": "Test", "tags": ["tag1", "tag2"]}
        result = render_frontmatter(data)
        assert result.startswith("---\n")
        assert result.endswith("---\n")
        assert "title: Test" in result
        assert "tags:" in result


class TestFormatMarkdown:
    """Test markdown formatting functionality."""

    def test_format_basic_markdown(self) -> None:
        text = "# Header\n\n\nParagraph with  extra  spaces."
        result = format_markdown(text)
        assert "# Header" in result
        assert "extra spaces" in result

    def test_format_with_invalid_markdown(self) -> None:
        text = "Some text"
        result = format_markdown(text)
        # Should not raise an exception
        assert result is not None


class TestGetFileCreationDate:
    """Test file creation date functionality."""

    def test_get_creation_date_existing_file(self, tmp_path: Path) -> None:
        # Create a temporary file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        date = get_file_creation_date(test_file)
        assert len(date) == 10  # YYYY-MM-DD format
        assert date.count("-") == 2

    def test_get_creation_date_nonexistent_file(self) -> None:
        # Should return current date when file doesn't exist
        nonexistent = Path("/nonexistent/file.md")
        date = get_file_creation_date(nonexistent)
        assert len(date) == 10  # YYYY-MM-DD format
        assert date.count("-") == 2


class TestExtractGranolaLink:
    """Test granola link extraction functionality."""

    def test_extract_granola_link_markdown_format(self) -> None:
        """Test extracting granola link from markdown format."""
        text = """# Meeting Notes

Some meeting content here.

Chat with meeting transcript: [https://notes.granola.ai/d/60e91e64-d482-4124-a609-1809862b4071](https://notes.granola.ai/d/60e91e64-d482-4124-a609-1809862b4071)

More content after the link."""

        url, body = extract_granola_link(text)
        assert url == "https://notes.granola.ai/d/60e91e64-d482-4124-a609-1809862b4071"
        assert "Chat with meeting transcript:" not in body
        assert "https://notes.granola.ai" not in body
        assert "# Meeting Notes" in body
        assert "More content after the link." in body

    def test_extract_granola_link_case_insensitive(self) -> None:
        """Test that granola link extraction is case insensitive."""
        text = "CHAT WITH MEETING TRANSCRIPT: [https://notes.granola.ai/d/123](https://notes.granola.ai/d/123)"

        url, body = extract_granola_link(text)
        assert url == "https://notes.granola.ai/d/123"
        assert "CHAT WITH MEETING TRANSCRIPT:" not in body

    def test_extract_granola_link_with_extra_whitespace(self) -> None:
        """Test granola link extraction with extra whitespace."""
        text = "Chat with meeting transcript:    [https://notes.granola.ai/d/456](https://notes.granola.ai/d/456)"

        url, body = extract_granola_link(text)
        assert url == "https://notes.granola.ai/d/456"
        assert "Chat with meeting transcript:" not in body

    def test_no_granola_link(self) -> None:
        """Test when there's no granola link in the text."""
        text = "# Meeting Notes\n\nJust some regular meeting content."

        url, body = extract_granola_link(text)
        assert url is None
        assert body == text

    def test_granola_link_with_different_url_format(self) -> None:
        """Test with different URL formats."""
        text = "Chat with meeting transcript: [http://example.com/transcript](http://example.com/transcript)"

        url, body = extract_granola_link(text)
        assert url == "http://example.com/transcript"
        assert "Chat with meeting transcript:" not in body

    def test_merge_frontmatter_with_meeting_transcript(self) -> None:
        """Test merging frontmatter with meeting transcript."""
        existing = {"title": "Meeting Notes", "tags": ["meeting"]}
        result = merge_frontmatter(
            existing, {"new-tag"}, "https://notes.granola.ai/d/123"
        )

        assert result["title"] == "Meeting Notes"
        assert "meeting" in result["tags"]
        assert "new-tag" in result["tags"]
        assert result["meeting-transcript"] == "https://notes.granola.ai/d/123"

    def test_merge_frontmatter_no_meeting_transcript(self) -> None:
        """Test merging frontmatter without meeting transcript."""
        existing = {"title": "Regular Notes"}
        result = merge_frontmatter(existing, {"tag1"}, None)

        assert result["title"] == "Regular Notes"
        assert "meeting-transcript" not in result


class TestExtractDateFromBody:
    """Test date extraction from body functionality."""

    def test_extract_iso_date(self) -> None:
        """Test extracting ISO format date."""
        text = """# Meeting Notes

Date: 2024-01-15

Some content here."""

        date = extract_date_from_body(text)
        assert date == "2024-01-15"

    def test_extract_us_date_format(self) -> None:
        """Test extracting US date format."""
        text = """# Meeting Notes

Meeting on 01/15/2024 about project updates.

Content here."""

        date = extract_date_from_body(text)
        assert date == "2024-01-15"

    def test_extract_european_date_format(self) -> None:
        """Test extracting European date format."""
        text = """# Meeting Notes

Date: 15/01/2024

Content here."""

        date = extract_date_from_body(text)
        assert date == "2024-01-15"

    def test_extract_long_date_format(self) -> None:
        """Test extracting long date format."""
        text = """# Meeting Notes

Meeting held on January 15, 2024 in the conference room.

Content here."""

        date = extract_date_from_body(text)
        assert date == "2024-01-15"

    def test_extract_short_date_format(self) -> None:
        """Test extracting short date format."""
        text = """# Meeting Notes

Date: Jan 15, 2024

Content here."""

        date = extract_date_from_body(text)
        assert date == "2024-01-15"

    def test_extract_date_with_dots(self) -> None:
        """Test extracting date with dots."""
        text = """# Meeting Notes

Date: 15.01.2024

Content here."""

        date = extract_date_from_body(text)
        assert date == "2024-01-15"

    def test_no_date_in_body(self) -> None:
        """Test when there's no date in the body."""
        text = """# Meeting Notes

Just some regular content without dates.

More content here."""

        date = extract_date_from_body(text)
        assert date is None

    def test_date_in_header_ignored(self) -> None:
        """Test that dates in headers are ignored."""
        text = """# Meeting Notes for 2024-01-15

Just some regular content.

More content here."""

        date = extract_date_from_body(text)
        assert date is None

    def test_date_beyond_first_10_lines_ignored(self) -> None:
        """Test that dates beyond first 10 lines are ignored."""
        text = """# Meeting Notes

Line 1
Line 2
Line 3
Line 4
Line 5
Line 6
Line 7
Line 8
Line 9
Line 10
Line 11 with date: 2024-01-15

Content here."""

        date = extract_date_from_body(text)
        assert date is None

    def test_first_date_found_is_used(self) -> None:
        """Test that the first date found is used."""
        text = """# Meeting Notes

First date: 2024-01-15
Second date: 2024-02-20

Content here."""

        date = extract_date_from_body(text)
        assert date == "2024-01-15"


class TestParseDateString:
    """Test date string parsing functionality."""

    def test_parse_iso_date(self) -> None:
        """Test parsing ISO date format."""
        result = parse_date_string("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_us_date(self) -> None:
        """Test parsing US date format."""
        result = parse_date_string("01/15/2024")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_european_date(self) -> None:
        """Test parsing European date format."""
        result = parse_date_string("15/01/2024")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_long_date(self) -> None:
        """Test parsing long date format."""
        result = parse_date_string("January 15, 2024")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_short_date(self) -> None:
        """Test parsing short date format."""
        result = parse_date_string("Jan 15, 2024")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_invalid_date(self) -> None:
        """Test parsing invalid date string."""
        result = parse_date_string("not a date")
        assert result is None

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string."""
        result = parse_date_string("")
        assert result is None


class TestMergeFrontmatterWithBodyDate:
    """Test frontmatter merging with date from body."""

    def test_merge_with_date_from_body(self) -> None:
        """Test that date from body is used when no created date exists."""
        body = """# Meeting Notes

Date: 2024-01-15

Content here."""

        result = merge_frontmatter(None, {"tag1"}, None, None, body)
        assert result["created"] == "2024-01-15"
        assert "tag1" in result["tags"]

    def test_merge_preserves_existing_created_date(self) -> None:
        """Test that existing created date is preserved."""
        existing = {"created": "2024-02-20"}
        body = """# Meeting Notes

Date: 2024-01-15

Content here."""

        result = merge_frontmatter(existing, {"tag1"}, None, None, body)
        assert result["created"] == "2024-02-20"  # Should preserve existing date
        assert "tag1" in result["tags"]

    def test_merge_falls_back_to_file_date(self) -> None:
        """Test that file creation date is used when no date in body."""
        # Create a temporary file for testing
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test")
            temp_path = Path(f.name)

        try:
            body = """# Meeting Notes

No date in this content."""

            result = merge_frontmatter(None, {"tag1"}, None, temp_path, body)
            assert "created" in result
            assert len(result["created"]) == 10  # YYYY-MM-DD format
            assert result["created"].count("-") == 2
            assert "tag1" in result["tags"]
        finally:
            temp_path.unlink()

    def test_merge_uses_earliest_date_between_body_and_file(self) -> None:
        """Test that the earliest date between body and file is used for created."""
        import os
        import tempfile
        from pathlib import Path

        # Create a temporary file with a specific creation date
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test")
            temp_path = Path(f.name)

        try:
            # Set file creation time to 2024-01-10 (earlier than body date)
            target_timestamp = datetime(2024, 1, 10).timestamp()
            os.utime(temp_path, (target_timestamp, target_timestamp))

            body = """# Meeting Notes

Date: 2024-01-15

Content here."""

            result = merge_frontmatter(None, {"tag1"}, None, temp_path, body)
            # Should use the earlier date (file creation date)
            assert result["created"] == "2024-01-10"
            assert "tag1" in result["tags"]
        finally:
            temp_path.unlink()

    def test_merge_uses_body_date_when_earlier_than_file(self) -> None:
        """Test that body date is used when it's earlier than file creation date."""
        import os
        import tempfile
        from pathlib import Path

        # Create a temporary file with a later creation date
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test")
            temp_path = Path(f.name)

        try:
            # Set file creation time to 2024-01-20 (later than body date)
            target_timestamp = datetime(2024, 1, 20).timestamp()
            os.utime(temp_path, (target_timestamp, target_timestamp))

            body = """# Meeting Notes

Date: 2024-01-15

Content here."""

            result = merge_frontmatter(None, {"tag1"}, None, temp_path, body)
            # Should use the earlier date (body date)
            assert result["created"] == "2024-01-15"
            assert "tag1" in result["tags"]
        finally:
            temp_path.unlink()

    def test_merge_adds_modification_date(self) -> None:
        """Test that modification date is always added from file metadata."""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test")
            temp_path = Path(f.name)

        try:
            body = """# Meeting Notes

Date: 2024-01-15

Content here."""

            result = merge_frontmatter(None, {"tag1"}, None, temp_path, body)
            assert "modified" in result
            assert len(result["modified"]) == 10  # YYYY-MM-DD format
            assert result["modified"].count("-") == 2
            assert "tag1" in result["tags"]
        finally:
            temp_path.unlink()

    def test_merge_updates_modification_date_when_different(self) -> None:
        """Test that modification date is updated when it differs from existing."""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test")
            temp_path = Path(f.name)

        try:
            existing = {"modified": "2024-01-01"}  # Old modification date
            body = """# Meeting Notes

Content here."""

            result = merge_frontmatter(existing, {"tag1"}, None, temp_path, body)
            # Should update to current file modification date
            assert "modified" in result
            assert result["modified"] != "2024-01-01"  # Should be updated
            assert "tag1" in result["tags"]
        finally:
            temp_path.unlink()

    def test_frontmatter_property_ordering(self) -> None:
        """Test that frontmatter properties are in the correct order: created, modified, meeting-transcript, tags."""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test")
            temp_path = Path(f.name)

        try:
            existing = {
                "title": "My Note",
                "author": "John Doe",
                "other_field": "value",
            }
            body = """# Meeting Notes

Date: 2024-01-15

Content here."""

            result = merge_frontmatter(
                existing,
                {"tag1", "tag2"},
                "https://example.com/transcript",
                temp_path,
                body,
            )

            # Check that properties exist
            assert "created" in result
            assert "modified" in result
            assert "meeting-transcript" in result
            assert "tags" in result

            # Convert to list to check order
            keys = list(result.keys())

            # Find indices of our key properties
            created_idx = keys.index("created")
            modified_idx = keys.index("modified")
            meeting_transcript_idx = keys.index("meeting-transcript")
            tags_idx = keys.index("tags")

            # Check the order: created < modified < meeting-transcript < tags
            assert created_idx < modified_idx, (
                f"created should come before modified, but got order: {keys}"
            )
            assert modified_idx < meeting_transcript_idx, (
                f"modified should come before meeting-transcript, but got order: {keys}"
            )
            assert meeting_transcript_idx < tags_idx, (
                f"meeting-transcript should come before tags, but got order: {keys}"
            )

            # Check that other properties come after our main properties
            title_idx = keys.index("title")
            author_idx = keys.index("author")
            other_field_idx = keys.index("other_field")

            assert tags_idx < title_idx, (
                f"tags should come before other properties, but got order: {keys}"
            )
            assert tags_idx < author_idx, (
                f"tags should come before other properties, but got order: {keys}"
            )
            assert tags_idx < other_field_idx, (
                f"tags should come before other properties, but got order: {keys}"
            )

        finally:
            temp_path.unlink()


class TestExtractTagsWithFixtures:
    """Test tag extraction with fixture files."""

    def test_no_front_matter_single_tag(self) -> None:
        """Test extracting a single tag from file without front-matter."""
        content = read_fixture("no_front_matter_single_tag.md")
        tags, body = extract_tags(content)
        assert "tag1" in tags

    def test_existing_front_matter_multiple_tags(self) -> None:
        """Test extracting multiple tags from file with existing front-matter."""
        content = read_fixture("existing_front_matter_multiple_tags.md")
        tags, body = extract_tags(content)
        assert {"tag1", "tag2", "tag3"}.issubset(tags)

    def test_no_tags_fixture(self) -> None:
        """Test extracting tags from file without any tags."""
        content = read_fixture("no_tags.md")
        tags, body = extract_tags(content)
        assert len(tags) == 0

    def test_no_front_matter_no_tags(self) -> None:
        """Test extracting tags from file with no front-matter and no tags."""
        content = read_fixture("no_front_matter_no_tags.md")
        tags, body = extract_tags(content)
        assert len(tags) == 0

    def test_edge_cases(self) -> None:
        """Test extracting tags from edge cases (should ignore tags in comments and code blocks)."""
        content = read_fixture("edge_cases.md")
        tags, body = extract_tags(content)
        # Should only extract real tags, not ones in comments or code blocks
        assert {"real-tag1", "real-tag2", "final-tag"}.issubset(tags)
        # Should NOT extract tags from comments and code blocks
        assert "fake-tag" not in tags  # From comment
        assert "code-tag" not in tags  # From inline code
        assert "world" not in tags  # From code block


class TestMergeFrontmatterWithFixtures:
    """Test frontmatter merging with fixture files."""

    def test_no_front_matter_single_tag(self) -> None:
        """Test adding front-matter to file without existing front-matter."""
        content = read_fixture("no_front_matter_single_tag.md")
        frontmatter, body = split_frontmatter(content)
        tags, _ = extract_tags(body)
        result = merge_frontmatter(frontmatter, tags)

        # Should add tags to frontmatter
        assert "tags" in result
        assert any("tag1" in str(tag) for tag in result["tags"])

    def test_existing_front_matter_multiple_tags(self) -> None:
        """Test merging tags into existing front-matter."""
        content = read_fixture("existing_front_matter_multiple_tags.md")
        frontmatter, body = split_frontmatter(content)
        tags, _ = extract_tags(body)
        result = merge_frontmatter(frontmatter, tags)

        # Should preserve existing front-matter
        assert "title" in result
        assert "author" in result
        # Should add tags
        assert "tags" in result
        assert len(result["tags"]) >= 3

    def test_no_tags_fixture(self) -> None:
        """Test merging empty tags list."""
        content = read_fixture("no_tags.md")
        frontmatter, body = split_frontmatter(content)
        tags, _ = extract_tags(body)
        result = merge_frontmatter(frontmatter, tags)

        # Should preserve existing front-matter
        assert "title" in result
        # Should not add tags section for empty tags
        assert "tags" not in result or len(result.get("tags", [])) == 0

    def test_edge_cases_merge(self) -> None:
        """Test merging tags extracted from edge cases."""
        content = read_fixture("edge_cases.md")
        frontmatter, body = split_frontmatter(content)
        tags, _ = extract_tags(body)
        result = merge_frontmatter(frontmatter, tags)

        # Should add tags to frontmatter
        assert "tags" in result
        tag_strings = [str(tag) for tag in result["tags"]]
        assert any("real-tag1" in tag for tag in tag_strings)
        assert any("real-tag2" in tag for tag in tag_strings)
        assert any("final-tag" in tag for tag in tag_strings)


class TestBackupAndRestore:
    """Test backup and restore functionality."""

    def test_create_vault_backup(self, tmp_path: Path) -> None:
        """Test creating a complete vault backup."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        # Create some test files
        (vault_root / "note1.md").write_text("# Note 1")
        (vault_root / "note2.md").write_text("# Note 2")
        subfolder = vault_root / "subfolder"
        subfolder.mkdir()
        (subfolder / "note3.md").write_text("# Note 3")

        # Create backup
        backup_path = create_vault_backup(vault_root)

        # Check that backup exists and contains all files
        assert backup_path.exists()
        assert (backup_path / "note1.md").exists()
        assert (backup_path / "note2.md").exists()
        assert (backup_path / "subfolder" / "note3.md").exists()

        # Check content is preserved
        assert (backup_path / "note1.md").read_text() == "# Note 1"
        assert (backup_path / "subfolder" / "note3.md").read_text() == "# Note 3"

    def test_create_vault_backup_with_custom_name(self, tmp_path: Path) -> None:
        """Test creating a vault backup with custom name."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()
        (vault_root / "note.md").write_text("# Note")

        backup_path = create_vault_backup(vault_root, "custom_backup")

        assert backup_path.name == "custom_backup"
        assert (backup_path / "note.md").exists()

    def test_clear_backups(self, tmp_path: Path) -> None:
        """Test clearing backup files."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        # Create backup structure
        backup_root = vault_root.parent / f"{vault_root.name}_backups"
        backup_root.mkdir()
        (backup_root / "note1.md.bak").write_text("backup content")
        (backup_root / "note2.md.bak").write_text("backup content")

        deleted_count = clear_backups(vault_root)

        assert deleted_count == 2
        assert not backup_root.exists()

    def test_restore_files(self, tmp_path: Path) -> None:
        """Test restoring files from backup."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        # Create original file
        original_file = vault_root / "note.md"
        original_file.write_text("original content")

        # Create backup
        backup_root = vault_root.parent / f"{vault_root.name}_backups"
        backup_root.mkdir()
        (backup_root / "note.md.bak").write_text("backup content")

        # Corrupt original file
        original_file.write_text("corrupted content")

        # Restore from backup
        restored_count = restore_files(vault_root)

        assert restored_count == 1
        assert original_file.read_text() == "backup content"

    def test_create_backup_path(self, tmp_path: Path) -> None:
        """Test creating backup path structure."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        file_path = vault_root / "subfolder" / "note.md"
        file_path.parent.mkdir()
        file_path.write_text("content")

        backup_path = create_backup_path(vault_root, file_path, ".bak")

        expected_path = (
            vault_root.parent
            / f"{vault_root.name}_backups"
            / "subfolder"
            / "note.md.bak"
        )
        assert backup_path == expected_path


class TestHelperFunctions:
    """Test helper functions."""

    def test_find_target_folder_for_tags(self) -> None:
        """Test finding target folder for tags."""
        # Test direct tag match
        assert _find_target_folder_for_tags(["products"]) == "products"
        assert _find_target_folder_for_tags(["projects"]) == "projects"

        # Test subtag match
        assert _find_target_folder_for_tags(["products/mobile"]) == "products/mobile"
        assert _find_target_folder_for_tags(["challenges/reach"]) == "challenges/reach"

        # Test olt/ prefixed tags
        assert _find_target_folder_for_tags(["olt/products"]) == "products"
        assert (
            _find_target_folder_for_tags(["olt/challenges/reach"]) == "challenges/reach"
        )

        # Test no match
        assert _find_target_folder_for_tags(["random"]) is None
        assert _find_target_folder_for_tags(["olt/random"]) is None

        # Test first match wins
        assert _find_target_folder_for_tags(["products", "projects"]) == "products"

    def test_move_file_to_folder(self, tmp_path: Path) -> None:
        """Test moving file to folder with backup."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        # Create source file
        source_file = vault_root / "source.md"
        source_file.write_text("content")

        # Create target directory
        target_dir = vault_root / "target"
        target_dir.mkdir()

        # Mock logger
        class MockLogger:
            def info(self, msg: str) -> None:
                pass

            def warning(self, msg: str) -> None:
                pass

        logger = MockLogger()

        # Move file
        result = _move_file_to_folder(
            source_file,
            target_dir,
            vault_root,
            ".bak",
            False,
            logger,
            "content",
            "target",
        )

        assert result is True
        assert (target_dir / "source.md").exists()
        assert not source_file.exists()

        # Check backup was created
        backup_path = vault_root.parent / f"{vault_root.name}_backups" / "source.md.bak"
        assert backup_path.exists()
        assert backup_path.read_text() == "content"

    def test_generate_meeting_filename(self, tmp_path: Path) -> None:
        """Test generating meeting filename."""
        # Create test file
        test_file = tmp_path / "test_meeting.md"
        test_file.write_text("content")

        # Test with frontmatter date
        frontmatter = {"created": "2024-01-15"}
        result = _generate_meeting_filename(test_file, frontmatter)
        assert result == "240115_test_meeting.md"

        # Test with no frontmatter (uses file creation date)
        result = _generate_meeting_filename(test_file, {})
        assert result is not None
        assert result.endswith("_test_meeting.md")
        assert len(result.split("_")[0]) == 6  # YYMMDD format

    def test_walk_markdown_files(self, tmp_path: Path) -> None:
        """Test walking markdown files."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        # Create test files
        (vault_root / "note1.md").write_text("content")
        (vault_root / "note2.txt").write_text("content")  # Non-markdown
        subfolder = vault_root / "subfolder"
        subfolder.mkdir()
        (subfolder / "note3.md").write_text("content")

        # Walk markdown files
        md_files = list(walk_markdown_files(vault_root))

        assert len(md_files) == 2
        assert vault_root / "note1.md" in md_files
        assert subfolder / "note3.md" in md_files
        assert vault_root / "note2.txt" not in md_files


class TestProcessFile:
    """Test process_file function."""

    def test_process_file_with_tags(self, tmp_path: Path) -> None:
        """Test processing file with tags."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        # Create test file with tags
        test_file = vault_root / "test.md"
        test_file.write_text("# Test\n\nThis has #tag1 and #tag2")

        # Mock logger
        class MockLogger:
            def info(self, msg: str) -> None:
                pass

            def error(self, msg: str) -> None:
                pass

        logger = MockLogger()

        # Process file
        stats = process_file(test_file, vault_root, False, ".bak", logger)

        assert stats["processed"] is True
        assert stats["added_tags"] == 2
        assert stats["removed_tags"] == 0

        # Check file was updated
        content = test_file.read_text()
        assert "---" in content  # Frontmatter added
        assert "tags:" in content
        assert "tag1" in content
        assert "tag2" in content
        assert "This has  and " in content  # Tags removed from body

    def test_process_file_dry_run(self, tmp_path: Path) -> None:
        """Test processing file in dry run mode."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        test_file = vault_root / "test.md"
        original_content = "# Test\n\nThis has #tag1"
        test_file.write_text(original_content)

        class MockLogger:
            def info(self, msg: str) -> None:
                pass

            def error(self, msg: str) -> None:
                pass

        logger = MockLogger()

        # Process file in dry run
        stats = process_file(test_file, vault_root, True, ".bak", logger)

        assert stats["processed"] is False  # No actual processing in dry run
        assert test_file.read_text() == original_content  # File unchanged


class TestProcessVault:
    """Test process_vault function."""

    def test_process_vault_all_files(self, tmp_path: Path) -> None:
        """Test processing entire vault."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        # Create test files
        (vault_root / "note1.md").write_text("# Note 1\n\n#tag1")
        (vault_root / "note2.md").write_text("# Note 2\n\n#tag2")
        subfolder = vault_root / "subfolder"
        subfolder.mkdir()
        (subfolder / "note3.md").write_text("# Note 3\n\n#tag3")

        class MockLogger:
            def info(self, msg: str) -> None:
                pass

            def error(self, msg: str) -> None:
                pass

        logger = MockLogger()

        # Process vault
        process_vault(str(vault_root), False, ".bak", logger)

        # Check all files were processed
        for file_path in [
            vault_root / "note1.md",
            vault_root / "note2.md",
            subfolder / "note3.md",
        ]:
            content = file_path.read_text()
            assert "---" in content  # Frontmatter added
            assert "tags:" in content

    def test_process_vault_specific_file(self, tmp_path: Path) -> None:
        """Test processing specific file in vault."""
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        # Create test files
        file1 = vault_root / "note1.md"
        file2 = vault_root / "note2.md"
        file1.write_text("# Note 1\n\n#tag1")
        file2.write_text("# Note 2\n\n#tag2")

        class MockLogger:
            def info(self, msg: str) -> None:
                pass

            def error(self, msg: str) -> None:
                pass

        logger = MockLogger()

        # Process only specific file
        process_vault(str(vault_root), False, ".bak", logger, specific_file=file1)

        # Check only file1 was processed
        assert "tags:" in file1.read_text()
        assert "tags:" not in file2.read_text()
