import json
from datetime import datetime, timedelta
from pathlib import Path

from crewai.tools import BaseTool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from langchain_google_community import CalendarToolkit
from pydantic import BaseModel, Field


def next_week_range(today: datetime):
    now = today
    days_ahead = (7 - now.weekday()) % 7
    next_monday = (now + timedelta(days=days_ahead)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = next_monday + timedelta(days=7)
    fmt = "%Y-%m-%d %H:%M:%S"
    return next_monday.strftime(fmt), end.strftime(fmt)


def find_credentials_file(filename: str) -> Path | None:
    """Search for credentials file in common locations.

    Searches in:
    1. Root directory (current working directory) - primary location
    2. Same directory as this file (fallback)
    3. User's home directory (fallback)

    Args:
        filename: Name of the file to search for (e.g., "credentials.json")

    Returns:
        Path to the file if found, None otherwise.
    """
    search_paths = [
        # Root directory (current working directory) - primary location
        Path.cwd() / filename,
        # Same directory as this file (fallback)
        Path(__file__).parent / filename,
        # User's home directory (fallback)
        Path.home() / filename,
    ]

    for path in search_paths:
        if path.exists() and path.is_file():
            return path

    return None


def load_google_credentials() -> Credentials:
    """Load and refresh Google OAuth credentials from token.json or credentials.json.

    First attempts to load from token.json. If that fails or doesn't exist,
    looks for credentials.json to initiate OAuth flow (though OAuth flow
    requires user interaction, so this is mainly for error messaging).

    Returns:
        Valid Credentials object.

    Raises:
        ValueError: If no valid credentials can be found or loaded.
    """
    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]

    # Try to find token.json first
    token_path = find_credentials_file("token.json")

    creds = None
    if token_path and token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), scopes)
        except Exception:
            # If loading fails, continue to check for credentials.json
            creds = None

    # If we have credentials but they're expired, try to refresh
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials back to token.json
                if token_path:
                    with token_path.open("w") as token_file:
                        token_file.write(creds.to_json())
            except Exception:
                # Refresh failed, will fall through to error handling
                creds = None

    # If we have valid credentials, return them
    if creds and creds.valid:
        return creds

    # If no valid credentials, check for credentials.json for better error message
    credentials_path = find_credentials_file("credentials.json")

    error_parts = [
        "No valid Google OAuth credentials found.",
    ]

    if token_path and token_path.exists():
        error_parts.append(
            f"Found token.json at {token_path} but it's invalid or expired."
        )
    else:
        error_parts.append("token.json not found.")

    if credentials_path:
        error_parts.append(
            f"Found credentials.json at {credentials_path}. "
            "You may need to run the OAuth flow to generate token.json."
        )
    else:
        error_parts.append(
            "credentials.json not found. Please ensure either token.json or "
            "credentials.json exists in a searchable location."
        )

    raise ValueError(" ".join(error_parts))


class GetNextWeekEventsInput(BaseModel):
    """Input schema for GetNextWeekEvents tool."""

    today: str = Field(
        ..., description="The date in the format YYYY-MM-DD as a string."
    )


class GetNextWeekEvents(BaseTool):
    name: str = "get_next_week_events"
    description: str = """
This is a tool to get the events in the user's calendar for the next week. As input, you should pass the date in the format YYYY-MM-DD as a string. As output, you will receive a list of events in the format of a JSON string. The objects will have the following properties:
    {
        "id": "...",
        "htmlLink": "...",
        "summary": "...",
        "creator": "...",
        "organizer": "...",
        "start": "2025-11-24T09:30:00Z",
        "end": "2025-11-24T10:00:00Z"
    }
"""

    args_schema: type[BaseModel] = GetNextWeekEventsInput

    def _run(self, today: str):
        today_datetime = datetime.strptime(today, "%Y-%m-%d")
        min_datetime, max_datetime = next_week_range(today_datetime)

        # Load and validate Google credentials (CalendarToolkit uses default credentials
        # from environment, but we validate they exist here for better error messages)
        _ = load_google_credentials()  # Validates credentials exist
        toolkit = CalendarToolkit()  # type: ignore[call-overload]
        tools = toolkit.get_tools()

        get_info = next(t for t in tools if t.name == "get_calendars_info")
        search_events = next(t for t in tools if t.name == "search_events")

        cal_dict = get_info.invoke({})
        cal_list = json.loads(cal_dict)

        target_ids = [
            "i32gqcmiqkfeduob47b6iueh1ou8a70t@import.calendar.google.com",
            "60b41fmboh551j37o7beq62uac@group.calendar.google.com",
        ]
        target_calendar_list = [c for c in cal_list if c["id"] in target_ids]

        calendars_info = json.dumps(target_calendar_list)  # back to JSON string

        result = search_events.invoke(
            {
                "calendars_info": calendars_info,
                "min_datetime": min_datetime,
                "max_datetime": max_datetime,
            }
        )

        return result
