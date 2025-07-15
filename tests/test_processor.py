"""Tests for the processor module."""

import os
from datetime import datetime
from pathlib import Path

from obsistant.processor import (
    extract_date_from_body,
    extract_granola_link,
    extract_tags,
    format_markdown,
    get_file_creation_date,
    merge_frontmatter,
    parse_date_string,
    render_frontmatter,
    split_frontmatter,
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
            assert (
                created_idx < modified_idx
            ), f"created should come before modified, but got order: {keys}"
            assert (
                modified_idx < meeting_transcript_idx
            ), f"modified should come before meeting-transcript, but got order: {keys}"
            assert (
                meeting_transcript_idx < tags_idx
            ), f"meeting-transcript should come before tags, but got order: {keys}"

            # Check that other properties come after our main properties
            title_idx = keys.index("title")
            author_idx = keys.index("author")
            other_field_idx = keys.index("other_field")

            assert (
                tags_idx < title_idx
            ), f"tags should come before other properties, but got order: {keys}"
            assert (
                tags_idx < author_idx
            ), f"tags should come before other properties, but got order: {keys}"
            assert (
                tags_idx < other_field_idx
            ), f"tags should come before other properties, but got order: {keys}"

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
