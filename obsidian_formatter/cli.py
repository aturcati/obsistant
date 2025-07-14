"""Command line interface for obsidian formatter."""

import click
import logging
from pathlib import Path
from .processor import process_vault


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Set up logger with appropriate level."""
    logger = logging.getLogger('obsidian_formatter')
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


@click.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--dry-run', '-n', is_flag=True, help='Show what would be done without making changes')
@click.option('--backup-ext', '-b', default='.bak', help='Backup file extension (default: .bak)')
@click.option('--format', '-f', 'format_markdown', is_flag=True, help='Format markdown files for consistent styling')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(vault_path: Path, dry_run: bool, backup_ext: str, format_markdown: bool, verbose: bool):
    """Process Obsidian vault to extract tags and add metadata.
    
    VAULT_PATH: Path to the Obsidian vault directory
    
    This tool will:
    - Extract #tags from markdown content and add them to frontmatter
    - Add creation date to frontmatter if not present
    - Optionally format markdown files for consistent styling
    - Create backup files before making changes
    """
    logger = setup_logger(verbose)
    
    if dry_run:
        logger.info(f"DRY RUN: Processing vault at {vault_path}")
    else:
        logger.info(f"Processing vault at {vault_path}")
    
    try:
        process_vault(
            root=str(vault_path),
            dry_run=dry_run,
            backup_ext=backup_ext,
            logger=logger,
            format_md=format_markdown
        )
        logger.info("Processing complete!")
    except Exception as e:
        logger.error(f"Error processing vault: {e}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    main()
