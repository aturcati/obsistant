"""Regression test for table corruption bug."""

import logging
import tempfile
from pathlib import Path

from obsistant.vault import process_vault


def test_table_corruption_regression() -> None:
    """Test that pipe tables are not corrupted during markdown formatting.

    This is a regression test for the table corruption bug where pipe tables
    get their rows collapsed into a single line during markdown formatting.
    """
    # Original table content
    original_content = """# Test Table

Here is a simple pipe table:

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1 Col 1 | Row 1 Col 2 | Row 1 Col 3 |
| Row 2 Col 1 | Row 2 Col 2 | Row 2 Col 3 |

This should be properly formatted as a table."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "test_table.md"

        # Write the test file
        test_file.write_text(original_content)

        # Process the file with formatting enabled
        process_vault(
            root=str(temp_path),
            dry_run=False,
            backup_ext=".bak",
            logger=logging.getLogger(),
            format_md=True,
            specific_file=test_file,
        )

        # Read the processed content
        processed_content = test_file.read_text()

        # The table should still have separate lines for each row
        # Currently this test will FAIL because of the bug
        lines = processed_content.split("\n")

        # Find the table section (after the frontmatter)
        table_lines = []
        in_table = False
        for line in lines:
            if line.startswith("|") and "Header" in line:
                in_table = True
            if in_table:
                if line.startswith("|"):
                    table_lines.append(line)
                elif line.strip() == "":
                    if table_lines:  # End of table
                        break

        # Assert that we have the expected number of table lines
        # Currently this will fail because all table content is collapsed into one line
        assert len(table_lines) >= 4, (
            f"Expected at least 4 table lines but got {len(table_lines)}: {table_lines}"
        )

        # Each row should be on a separate line
        assert "Header 1" in table_lines[0]
        assert "Row 1 Col 1" in table_lines[2]  # After header separator
        assert "Row 2 Col 1" in table_lines[3]


if __name__ == "__main__":
    test_table_corruption_regression()
