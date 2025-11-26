"""Pydantic models for calendar crew tasks."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CalendarEvent(BaseModel):
    """Model for calendar events from get_next_week_events_task."""

    calendar: str = Field(..., description="The calendar name")
    title: str | None = Field(default="(No Title)", description="Event title")
    date: str = Field(..., description="Event date")
    start_time: str = Field(..., description="Event start time")
    end_time: str = Field(..., description="Event end time")
    attendees: list[str] = Field(default_factory=list, description="List of attendees")
    location: str | None = Field(None, description="Event location")
    description: str | None = Field(None, description="Event description")

    @field_validator("title", mode="before")
    @classmethod
    def ensure_title_not_none(cls, v):
        """Convert None title to default value."""
        return v if v is not None else "(No Title)"

    @field_validator("location", "description", mode="before")
    @classmethod
    def normalize_optional_strings(cls, v):
        """Convert string 'None' or empty strings to None."""
        if v is None:
            return None
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped == "" or v_stripped.lower() == "none":
                return None
        return v


class CalendarEventsList(BaseModel):
    """Wrapper model for a list of calendar events."""

    events: list[CalendarEvent] = Field(..., description="List of calendar events")


class ConcertEvent(BaseModel):
    """Model for concert events from research_concerts_task."""

    artist: str = Field(..., description="Artist name")
    date: str = Field(..., description="Event date")
    start_time: str | None = Field(None, description="Event start time")
    end_time: str | None = Field(None, description="Event end time")
    location: str | None = Field(None, description="Event location")
    artist_description: str | None = Field(None, description="Summary of the artist")
    price: str | None = Field(None, description="Ticket price")
    spotify_link: str | None = Field(None, description="Link to artist's Spotify page")

    @field_validator(
        "location",
        "price",
        "spotify_link",
        "artist_description",
        "start_time",
        "end_time",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(cls, v):
        """Convert string 'None' or empty strings to None."""
        if v is None:
            return None
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped == "" or v_stripped.lower() == "none":
                return None
        return v


class ConcertEventsList(BaseModel):
    """Wrapper model for a list of concert events."""

    concerts: list[ConcertEvent] = Field(..., description="List of concert events")
