"""Google Calendar OAuth authentication for obsistant."""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def authenticate_google_calendar(
    vault_path: Path,
    credentials_path: Path,
    token_path: Path,
) -> Credentials:
    """Authenticate with Google Calendar API.

    Loads existing token.json if present and valid, refreshes if expired,
    or runs OAuth flow if no valid credentials exist.

    Args:
        vault_path: Path to the vault root directory.
        credentials_path: Path to credentials.json file (relative to vault_path or absolute).
        token_path: Path to token.json file (relative to vault_path or absolute).

    Returns:
        Valid Credentials object.

    Raises:
        FileNotFoundError: If credentials.json is not found.
        ValueError: If authentication fails.
    """
    # Resolve paths relative to vault_path if not absolute
    if not credentials_path.is_absolute():
        credentials_path = vault_path / credentials_path
    if not token_path.is_absolute():
        token_path = vault_path / token_path

    creds = None

    # Try to load existing token.json
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception:
            # If loading fails, continue to OAuth flow
            creds = None

    # If we have credentials but they're expired, try to refresh
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials back to token.json
                token_path.parent.mkdir(parents=True, exist_ok=True)
                with token_path.open("w") as token_file:
                    token_file.write(creds.to_json())
            except Exception:
                # Refresh failed, will fall through to OAuth flow
                creds = None

    # If we have valid credentials, return them
    if creds and creds.valid:
        return creds

    # No valid credentials, need to run OAuth flow
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {credentials_path}. "
            "Please place your Google OAuth credentials file there."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with token_path.open("w") as token:
        token.write(creds.to_json())

    return creds
