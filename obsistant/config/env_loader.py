"""Environment variable loader for vault-specific .env files."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_vault_env(vault_path: Path | str | None) -> bool:
    """Load environment variables from .obsistant/.env in the vault.

    Args:
        vault_path: Path to the vault root directory. If None, returns False
            without loading any environment variables.

    Returns:
        True if .env file was found and loaded, False otherwise.
    """
    if vault_path is None:
        return False

    vault_path_obj = Path(vault_path)
    env_path = vault_path_obj / ".obsistant" / ".env"

    if not env_path.exists():
        return False

    # Load .env file using absolute path for consistent behavior
    load_dotenv(env_path.resolve(), override=False)
    return True
