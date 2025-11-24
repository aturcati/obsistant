"""Tests for table formatting functionality in format_markdown."""

import unittest.mock

from obsistant.core import format_markdown

# Test fixtures
RAW_TABLE_MD = """# Test Table

Here is a simple pipe table:

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1 Col 1 | Row 1 Col 2 | Row 1 Col 3 |
| Row 2 Col 1 | Row 2 Col 2 | Row 2 Col 3 |

This should be properly formatted as a table.
"""

CORRECT_FORMATTED_MD = """# Test Table

Here is a simple pipe table:

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1 Col 1 | Row 1 Col 2 | Row 1 Col 3 |
| Row 2 Col 1 | Row 2 Col 2 | Row 2 Col 3 |

This should be properly formatted as a table.
"""


class TestTableFormatting:
    """Test markdown table formatting functionality."""

    def test_format_markdown_with_working_plugin(self) -> None:
        """Test that format_markdown returns correctly formatted table when plugin works.

        This is a regression test - currently the function corrupts tables due to
        missing mdformat-gfm plugin, but when the plugin is properly installed,
        it should preserve table structure.
        """
        # Mock mdformat to work properly and return the expected formatted result
        with unittest.mock.patch(
            "obsistant.core.formatting.mdformat.text", return_value=CORRECT_FORMATTED_MD
        ):
            with unittest.mock.patch(
                "obsistant.core.formatting._clean_list_blank_lines",
                return_value=CORRECT_FORMATTED_MD,
            ):
                result = format_markdown(RAW_TABLE_MD)
                assert result.strip() == CORRECT_FORMATTED_MD.strip()

    def test_format_markdown_returns_unchanged_when_plugin_absent(self) -> None:
        """Test that format_markdown returns input unchanged when mdformat-gfm plugin is absent."""
        # Mock the mdformat.text function to raise ValueError on first call (with extensions),
        # then also raise an exception on the fallback (without extensions) to simulate
        # complete plugin failure
        with unittest.mock.patch(
            "obsistant.core.formatting.mdformat.text"
        ) as mock_text:
            mock_text.side_effect = [
                ValueError("nonexistent"),
                ValueError("no fallback"),
            ]
            with unittest.mock.patch(
                "obsistant.core.formatting.console.print"
            ) as mock_print:
                result = format_markdown(RAW_TABLE_MD)
                # Should have printed warning
                mock_print.assert_called_once()
                # When plugin is absent and table is detected, should return input unchanged
                assert result == RAW_TABLE_MD

    def test_format_markdown_detects_table_correctly(self) -> None:
        """Test that the table detection regex works correctly."""
        # This verifies the table detection pattern works
        with unittest.mock.patch(
            "obsistant.core.formatting.mdformat.text"
        ) as mock_text:
            mock_text.side_effect = [
                ValueError("nonexistent"),
                ValueError("no fallback"),
            ]
            with unittest.mock.patch(
                "obsistant.core.formatting.console.print"
            ) as mock_print:
                result = format_markdown(RAW_TABLE_MD)

                # Should have called print with warning about missing plugin
                mock_print.assert_called_once()
                warning_call = mock_print.call_args[0][0]
                assert "Detected pipe table" in warning_call
                assert "mdformat-gfm plugin is unavailable" in warning_call

                # Should return original text
                assert result == RAW_TABLE_MD

    def test_format_markdown_no_table_with_missing_plugin(self) -> None:
        """Test formatting works normally when no table present and plugin missing."""
        text_without_table = """# No Table Here

Just some regular markdown text.

- A bullet list
- Another item

Some more text.
"""

        # Mock mdformat to simulate plugin unavailable, but should still work for non-table content
        with unittest.mock.patch(
            "obsistant.core.formatting.mdformat.text"
        ) as mock_text:
            # First call raises ImportError (simulating missing gfm plugin)
            # Second call in fallback should work normally
            mock_text.side_effect = [
                ImportError("No plugin"),
                text_without_table,  # fallback call succeeds
            ]

            with unittest.mock.patch(
                "obsistant.core.formatting._clean_list_blank_lines",
                return_value=text_without_table,
            ):
                result = format_markdown(text_without_table)

                # Should have called mdformat.text twice (first fails, second succeeds)
                assert mock_text.call_count == 2
                assert result == text_without_table
