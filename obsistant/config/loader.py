"""Configuration loader for obsistant."""

from __future__ import annotations

from pathlib import Path

import yaml

from .schema import Config


def load_config(vault_root: Path) -> Config | None:
    """Load configuration from config.yaml in .obsistant folder.

    Args:
        vault_root: Path to the vault root directory.

    Returns:
        Config object if config.yaml exists, None otherwise.
    """
    config_path = vault_root / ".obsistant" / "config.yaml"
    if not config_path.exists():
        return None

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return None
            # Use from_dict which handles YAML structure transformation and backward compatibility
            return Config.from_dict(data)
    except (OSError, yaml.YAMLError, Exception):
        # Log error but don't fail - return None to use defaults
        # Exception catches Pydantic validation errors
        return None


def save_config(config: Config, vault_root: Path) -> None:
    """Save configuration to config.yaml in .obsistant folder.

    Args:
        config: Config object to save.
        vault_root: Path to the vault root directory.
    """
    config_path = vault_root / ".obsistant" / "config.yaml"
    # Ensure .obsistant directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config.to_yaml(), encoding="utf-8")
