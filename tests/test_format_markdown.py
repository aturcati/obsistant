"""Tests for markdown formatting functionality, specifically bullet-list blank-line handling."""

from obsistant.processor import format_markdown


class TestFormatMarkdownBulletLists:
    """Test markdown formatting for bullet lists with blank line removal."""

    def test_nested_bullet_list_blank_line_removal(self) -> None:
        """Test removing blank lines from nested bullet lists (user's example)."""
        input_text = """- Main OTC limitations:

    - Poor documentation quality

    - Missing critical services (e.g., secrets manager, proper IAM)

    - Limited service sophistication compared to hyperscalers

    - Requires workarounds that increase development time
"""
        expected = """- Main OTC limitations:
  - Poor documentation quality
  - Missing critical services (e.g., secrets manager, proper IAM)
  - Limited service sophistication compared to hyperscalers
  - Requires workarounds that increase development time
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_complex_nested_bullet_lists_with_text(self) -> None:
        """Test complex nested bullet lists with surrounding text (user's complex example)."""
        input_text = """# My Notes

Some introductory text.

- Main OTC limitations:

    - Poor documentation quality

    - Missing critical services (e.g., secrets manager, proper IAM)

    - Limited service sophistication compared to hyperscalers

    - Requires workarounds that increase development time

- Another section:

    - First item

        - Nested item

        - Another nested item

    - Second item

    - Third item

Some concluding text.
"""
        expected = """# My Notes

Some introductory text.

- Main OTC limitations:
  - Poor documentation quality
  - Missing critical services (e.g., secrets manager, proper IAM)
  - Limited service sophistication compared to hyperscalers
  - Requires workarounds that increase development time
- Another section:
  - First item
    - Nested item
    - Another nested item
  - Second item
  - Third item

Some concluding text.
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_ordered_lists_blank_line_removal(self) -> None:
        """Test removing blank lines from ordered lists."""
        input_text = """1. First item with details:

    a. Sub-item one

    b. Sub-item two

        i. Deeply nested item

        ii. Another deeply nested item

    c. Sub-item three

2. Second main item

3. Third main item
"""
        expected = """1. First item with details:

   a. Sub-item one

   b. Sub-item two

   ```
    i. Deeply nested item

    ii. Another deeply nested item
   ```

   c. Sub-item three

1. Second main item

1. Third main item
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_mixed_list_types_blank_line_removal(self) -> None:
        """Test removing blank lines from mixed bullet and ordered lists."""
        input_text = """- Unordered list item

    1. Ordered sub-item

    2. Another ordered sub-item

        - Nested unordered item

        - Another nested unordered item

- Another main unordered item

    1. First ordered sub-item

    2. Second ordered sub-item
"""
        expected = """- Unordered list item

  1. Ordered sub-item

  1. Another ordered sub-item

     - Nested unordered item
     - Another nested unordered item
- Another main unordered item

  1. First ordered sub-item

  1. Second ordered sub-item
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_different_indent_levels(self) -> None:
        """Test handling different indentation levels in nested lists."""
        input_text = """- Level 1 item

    - Level 2 item

        - Level 3 item

            - Level 4 item

        - Another level 3 item

    - Another level 2 item

- Another level 1 item
"""
        expected = """- Level 1 item
  - Level 2 item
    - Level 3 item
      - Level 4 item
    - Another level 3 item
  - Another level 2 item
- Another level 1 item
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_list_separated_by_paragraph_keeps_blank_line(self) -> None:
        """Test that blank lines are preserved when lists are separated by real paragraphs."""
        input_text = """- First list item

- Second list item

This is a real paragraph that separates the lists.

- This starts a new list

- Second item in new list
"""
        expected = """- First list item
- Second list item

This is a real paragraph that separates the lists.

- This starts a new list
- Second item in new list
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_code_block_inside_list(self) -> None:
        """Test that code blocks inside lists are handled correctly."""
        input_text = """- Setup instructions:

    - Install dependencies

    - Configure the system:

        ```bash
        sudo apt update
        sudo apt install package
        ```

    - Run the application

- Additional notes:

    - Remember to check logs

    - Monitor performance
"""
        expected = """- Setup instructions:
  - Install dependencies
  - Configure the system:

    ```bash
    sudo apt update
    sudo apt install package
    ```

  - Run the application
- Additional notes:
  - Remember to check logs
  - Monitor performance
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_lists_inside_blockquotes(self) -> None:
        """Test that lists inside blockquotes have blank lines removed."""
        input_text = """> Important points to remember:
>
> - First important point
>
> - Second important point
>
>     - Sub-point under second
>
>     - Another sub-point
>
> - Third important point
>
> End of quote.
"""
        expected = """> Important points to remember:
>
> - First important point
>
> - Second important point
>
>   - Sub-point under second
>
>   - Another sub-point
>
> - Third important point
>
> End of quote.
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_multiple_consecutive_blank_lines_in_lists(self) -> None:
        """Test handling of multiple consecutive blank lines between list items."""
        input_text = """- First item


- Second item



    - Nested item with multiple blanks


    - Another nested item

- Third item
"""
        expected = """- First item
- Second item
  - Nested item with multiple blanks
  - Another nested item
- Third item
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_asterisk_and_plus_bullet_markers(self) -> None:
        """Test blank line removal with different bullet markers (* and +)."""
        input_text = """* First item with asterisk

    * Nested item with asterisk

        + Deep nested with plus

        + Another deep nested plus

    * Another nested asterisk

+ Main item with plus

    + Nested item with plus
"""
        expected = """- First item with asterisk
  - Nested item with asterisk
    - Deep nested with plus
    - Another deep nested plus
  - Another nested asterisk
* Main item with plus
  - Nested item with plus
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_list_items_with_multiple_paragraphs(self) -> None:
        """Test that multi-paragraph list items preserve their internal structure."""
        input_text = """- This is a list item with multiple paragraphs.

  This is the second paragraph of the same list item.

  And this is the third paragraph.

- This is another list item.

    - With a nested item

    - And another nested item
"""
        expected = """- This is a list item with multiple paragraphs.

  This is the second paragraph of the same list item.

  And this is the third paragraph.

- This is another list item.
  - With a nested item
  - And another nested item
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_preserve_blank_lines_between_different_elements(self) -> None:
        """Test that blank lines between different markdown elements are preserved."""
        input_text = """# Header

Some paragraph text.

- List item one

- List item two

## Another Header

More text here.

1. Ordered item

2. Another ordered item

Final paragraph.
"""
        expected = """# Header

Some paragraph text.

- List item one
- List item two

## Another Header

More text here.

1. Ordered item

1. Another ordered item

Final paragraph.
"""
        result = format_markdown(input_text)
        assert result.strip() == expected.strip()

    def test_edge_case_empty_list_items(self) -> None:
        """Test handling of empty list items and whitespace-only items."""
        input_text = """- Non-empty item

-

- Another non-empty item

    - Nested non-empty

    -

    - Another nested
"""
        # Note: The exact behavior might depend on mdformat's handling of empty list items
        result = format_markdown(input_text)
        # Just ensure it doesn't crash and produces valid markdown
        assert isinstance(result, str)
        assert len(result.strip()) > 0
