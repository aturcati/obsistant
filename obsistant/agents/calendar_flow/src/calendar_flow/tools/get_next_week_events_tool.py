import json
from datetime import datetime, timedelta
from pathlib import Path

from crewai.tools import BaseTool
from google.oauth2.credentials import Credentials
from langchain_google_community import CalendarToolkit
from pydantic import BaseModel, Field

from obsistant.config.loader import load_config
from obsistant.core.calendar_auth import authenticate_google_calendar


def next_week_range(today: datetime):
    now = today
    days_ahead = (7 - now.weekday()) % 7
    next_monday = (now + timedelta(days=days_ahead)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = next_monday + timedelta(days=7)
    fmt = "%Y-%m-%d %H:%M:%S"
    return next_monday.strftime(fmt), end.strftime(fmt)


def load_google_credentials(vault_path: Path) -> Credentials:
    """Load and refresh Google OAuth credentials using config paths.

    Loads credentials from paths specified in .obsistant/config.yaml.

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        Valid Credentials object.

    Raises:
        ValueError: If no valid credentials can be found or loaded.
    """
    # Load config to get credential paths
    config = load_config(vault_path)
    if not config:
        raise ValueError(
            f"Could not load .obsistant/config.yaml from vault at {vault_path}. "
            "Please run 'obsistant init' first."
        )

    credentials_path = Path(config.calendar.credentials_path)
    token_path = Path(config.calendar.token_path)

    # Resolve paths relative to vault_path if not absolute
    if not credentials_path.is_absolute():
        credentials_path = vault_path / credentials_path
    if not token_path.is_absolute():
        token_path = vault_path / token_path

    # Use authenticate_google_calendar which handles loading, refreshing, and OAuth flow
    try:
        return authenticate_google_calendar(vault_path, credentials_path, token_path)
    except FileNotFoundError as e:
        raise ValueError(
            f"credentials.json not found at {credentials_path}. "
            "Please run 'obsistant calendar-login' to authenticate."
        ) from e
    except Exception as e:
        raise ValueError(
            f"Failed to load Google credentials: {e}. "
            "Please run 'obsistant calendar-login' to authenticate."
        ) from e


class GetNextWeekEventsInput(BaseModel):
    """Input schema for GetNextWeekEvents tool."""

    today: str = Field(
        ..., description="The date in the format YYYY-MM-DD as a string."
    )
    vault_path: str = Field(
        ..., description="The path to the Obsidian vault directory."
    )


class GetNextWeekEvents(BaseTool):
    name: str = "get_next_week_events"
    description: str = """
This is a tool to get the events in the user's calendar for the next week. As input, you should pass the date in the format YYYY-MM-DD as a string and the vault_path also as a string. The vault_path is the path to the Obsidian vault directory and it is necessary to access the .obsistant/config.yaml file necessary to get the calendar IDs. As output, you will receive a list of events in the format of a JSON string. The objects will have the following properties:
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

    def _run(self, today: str, vault_path: str | None = None):
        if not vault_path:
            raise ValueError("vault_path is required to load calendar configuration")

        vault_path_obj = Path(vault_path)
        today_datetime = datetime.strptime(today, "%Y-%m-%d")
        min_datetime, max_datetime = next_week_range(today_datetime)

        # Load and validate Google credentials using config paths
        # CalendarToolkit uses default credentials from environment, but we validate they exist
        _ = load_google_credentials(vault_path_obj)
        toolkit = CalendarToolkit()  # type: ignore[call-overload]
        tools = toolkit.get_tools()

        get_info = next(t for t in tools if t.name == "get_calendars_info")
        search_events = next(t for t in tools if t.name == "search_events")

        cal_dict = get_info.invoke({})
        cal_list = json.loads(cal_dict)

        config = load_config(Path(vault_path))
        if not config:
            raise ValueError(
                f"Could not load .obsistant/config.yaml from vault at {vault_path}"
            )

        target_ids = list(config.calendar.calendars.values())
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
