"""Processing logic for obsidian formatter."""

import re
from pathlib import Path
from typing import Iterator, Tuple, Set, Dict, Optional
import yaml
import mdformat
from datetime import datetime
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import log_change, console

TAG_REGEX = r"(?<!\w)#([\w/-]+)"


def walk_markdown_files(root: Path) -> Iterator[Path]:
    """Walk through the directory to find .md files."""
    return root.rglob('*.md')


def split_frontmatter(text: str) -> Tuple[Optional[Dict], str]:
    """Split the front matter and return it with the content."""
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                content = parts[2]
                return frontmatter, content
            except yaml.YAMLError:
                # If YAML parsing fails, treat as no frontmatter
                return None, text
    return None, text


def extract_tags(body: str) -> Tuple[Set[str], str]:
    """Use regex to extract tags from the content."""
    tags = set(re.findall(TAG_REGEX, body))
    return tags, body


def get_file_creation_date(path: Path) -> str:
    """Get the file creation date in ISO format."""
    try:
        # On macOS, use st_birthtime for creation time
        stat = path.stat()
        if hasattr(stat, 'st_birthtime'):
            # macOS/BSD creation time
            creation_time = stat.st_birthtime
        else:
            # Fallback to modification time on other systems
            creation_time = stat.st_mtime
        
        # Convert to ISO format date string
        return datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d')
    except OSError:
        # If we can't get the creation date, use current date
        return datetime.now().strftime('%Y-%m-%d')


def merge_frontmatter(orig: Optional[Dict], tags: Set[str], file_path: Optional[Path] = None) -> Dict:
    """Merge tags and creation date into existing front matter ensuring no duplication."""
    if orig is None:
        orig = {}
    
    # Get existing tags, ensuring they're treated as a set
    orig_tags = set(orig.get('tags', []))
    
    # Merge with new tags
    merged_tags = orig_tags.union(tags)
    
    # Only set tags if we have any
    if merged_tags:
        orig['tags'] = sorted(merged_tags)
    elif 'tags' not in orig:
        # Don't add empty tags field if there were no tags originally
        pass
    
    # Add creation date if not already present and file path is provided
    if file_path and 'created' not in orig:
        orig['created'] = get_file_creation_date(file_path)
    
    return orig


def render_frontmatter(data: Dict) -> str:
    """Convert the data back to front matter format."""
    return '---\n' + yaml.safe_dump(data) + '---\n'


def format_markdown(text: str) -> str:
    """Format markdown text using mdformat for consistent styling."""
    try:
        return mdformat.text(text, options={
            'wrap': 'no',  # Don't wrap lines
            'number': False,  # Don't number lists
        })
    except Exception as e:
        # If formatting fails, return original text
        return text


def process_file(path: Path, dry_run: bool, backup_ext: str, logger, format_md: bool = False):
    """Process each file: read, modify, and write with a backup.
    
    Returns:
        dict: Statistics about the processing (added_tags, removed_tags, processed)
    """
    stats = {'added_tags': 0, 'removed_tags': 0, 'processed': False}
    
    try:
        with path.open('r', encoding='utf-8') as file:
            text = file.read()
    except (OSError, UnicodeDecodeError) as e:
        logger.error(f'Error reading {path}: {e}')
        return stats

    frontmatter, body = split_frontmatter(text)
    tags, body = extract_tags(body)
    
    # Always process files to potentially add creation date
    original_frontmatter = frontmatter.copy() if frontmatter else None
    new_frontmatter = merge_frontmatter(frontmatter, tags, path)
    
    # Calculate tag changes
    original_tags = set(original_frontmatter.get('tags', [])) if original_frontmatter else set()
    new_tags = set(new_frontmatter.get('tags', [])) if new_frontmatter else set()
    added_tags = new_tags - original_tags
    removed_tags = original_tags - new_tags
    
    # Check if we need to process this file
    needs_processing = (
        bool(tags) or 
        frontmatter is not None or 
        format_md or 
        new_frontmatter != original_frontmatter  # Creation date was added
    )
    
    if not needs_processing:
        logger.info(f'No changes needed for {path}')
        return stats
    
    # Format markdown if requested
    if format_md:
        body = format_markdown(body)
    
    # Only add frontmatter if we have content for it
    if new_frontmatter:
        new_text = render_frontmatter(new_frontmatter) + body
    else:
        new_text = body
    
    # Only write if content has changed
    if new_text != text:
        stats['processed'] = True
        stats['added_tags'] = len(added_tags)
        stats['removed_tags'] = len(removed_tags)
        
        # Use rich logging for changes
        if added_tags or removed_tags:
            log_change(path, added_tags, removed_tags, dry_run)
        
        if not dry_run:
            try:
                backup_path = path.with_suffix(path.suffix + backup_ext)
                # Create backup by copying, then overwrite original
                backup_path.write_text(text, encoding='utf-8')
                path.write_text(new_text, encoding='utf-8')
                actions = []
                if tags:
                    actions.append(f'added {len(tags)} tags')
                if format_md:
                    actions.append('formatted markdown')
                if original_frontmatter != new_frontmatter and 'created' in new_frontmatter:
                    if original_frontmatter is None or 'created' not in original_frontmatter:
                        actions.append('added creation date')
                logger.info(f'Processed {path} - {" and ".join(actions)} (backup: {backup_path})')
            except OSError as e:
                logger.error(f'Error writing {path}: {e}')
                stats['processed'] = False
                return stats
        else:
            actions = []
            if tags:
                actions.append(f'add {len(tags)} tags')
            if format_md:
                actions.append('format markdown')
            if original_frontmatter != new_frontmatter and 'created' in new_frontmatter:
                if original_frontmatter is None or 'created' not in original_frontmatter:
                    actions.append('add creation date')
            logger.info(f'[DRY RUN] Would process {path} - {" and ".join(actions)}')
    else:
        logger.info(f'No changes needed for {path}')
    
    return stats


def process_vault(root: str, dry_run: bool, backup_ext: str, logger, format_md: bool = False):
    """Orchestrate processing of the entire vault and provide summary statistics."""
    total_added_tags = 0
    total_removed_tags = 0
    total_processed_files = 0

    for markdown_file in walk_markdown_files(Path(root)):
        stats = process_file(markdown_file, dry_run, backup_ext, logger, format_md)
        total_added_tags += stats['added_tags']
        total_removed_tags += stats['removed_tags']
        if stats['processed']:
            total_processed_files += 1

    # Print summary statistics using rich
    console.print(f"[bold green]Vault Processing Summary[/]")
    console.print(f"Total files processed: [bold]{total_processed_files}[/]")
    console.print(f"Total tags added: [bold]{total_added_tags}[/]")
    console.print(f"Total tags removed: [bold]{total_removed_tags}[/]")
