"""Backup and restore operations for obsistant."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def create_backup_path(vault_root: Path, file_path: Path, backup_ext: str) -> Path:
    """Create backup path that mirrors the vault structure in a backup folder."""
    backup_root = vault_root.parent / f"{vault_root.name}_backups"
    relative_path = file_path.relative_to(vault_root)
    backup_path = backup_root / relative_path
    backup_path = backup_path.with_suffix(backup_path.suffix + backup_ext)
    return backup_path


def clear_backups(vault_root: Path) -> int:
    """Clear all backup files for a vault. Returns count of deleted files."""
    backup_root = vault_root.parent / f"{vault_root.name}_backups"
    if not backup_root.exists():
        return 0
    deleted_count = 0
    for backup_file in backup_root.rglob("*"):
        if backup_file.is_file():
            backup_file.unlink()
            deleted_count += 1
    for backup_dir in sorted(
        backup_root.rglob("*"), key=lambda x: str(x), reverse=True
    ):
        if backup_dir.is_dir() and not any(backup_dir.iterdir()):
            backup_dir.rmdir()
    if backup_root.exists() and not any(backup_root.iterdir()):
        backup_root.rmdir()
    return deleted_count


def restore_files(
    vault_root: Path, specific_file: Path | None = None, backup_ext: str = ".bak"
) -> int:
    """Restore corrupted files from backups. Returns count of restored files."""
    backup_root = vault_root.parent / f"{vault_root.name}_backups"
    if not backup_root.exists():
        return 0
    restored_count = 0
    if specific_file:
        backup_path = create_backup_path(vault_root, specific_file, backup_ext)
        if backup_path.exists():
            try:
                backup_content = backup_path.read_text(encoding="utf-8")
                specific_file.write_text(backup_content, encoding="utf-8")
                restored_count = 1
            except (OSError, UnicodeDecodeError):
                pass
    else:
        for backup_file in backup_root.rglob(f"*{backup_ext}"):
            if backup_file.is_file():
                try:
                    relative_path = backup_file.relative_to(backup_root)
                    original_relative_path = relative_path.with_suffix(
                        relative_path.suffix.replace(backup_ext, "")
                    )
                    original_path = vault_root / original_relative_path
                    backup_content = backup_file.read_text(encoding="utf-8")
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    original_path.write_text(backup_content, encoding="utf-8")
                    restored_count += 1
                except (OSError, UnicodeDecodeError):
                    continue
    return restored_count


def create_vault_backup(vault_root: Path, backup_name: str | None = None) -> Path:
    """Create a complete backup of the vault."""
    if backup_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{vault_root.name}_{timestamp}"
    backup_dir = vault_root.parent / backup_name
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(vault_root, backup_dir)
    return backup_dir
