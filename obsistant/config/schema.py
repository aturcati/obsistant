"""Configuration schema for obsistant."""

from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field


class VaultFoldersConfig(BaseModel):
    """Configuration for vault folder names."""

    quick_notes: str = "00-Quick Notes"
    meetings: str = "10-Meetings"
    notes: str = "20-Notes"
    guides: str = "30-Guides"
    vacations: str = "40-Vacations"
    files: str = "50-Files"


class TagsConfig(BaseModel):
    """Configuration for tag processing."""

    target_tags: list[str] = Field(
        default_factory=lambda: [
            "products",
            "projects",
            "devops",
            "challenges",
            "events",
        ]
    )
    ignored_tags: list[str] = Field(default_factory=lambda: ["olt"])
    tag_regex: str = r"(?<!\w)#([\w/-]+)(?=\s|$)"


class MeetingsConfig(BaseModel):
    """Configuration for meeting processing."""

    filename_format: str = "YYMMDD_Title"
    archive_weeks: int = 2
    auto_tag: str = "meeting"


class ProcessingConfig(BaseModel):
    """Configuration for general processing."""

    backup_ext: str = ".bak"
    date_formats: list[str] = Field(
        default_factory=lambda: [
            "%Y-%m-%d",  # 2024-01-15
            "%Y/%m/%d",  # 2024/01/15
            "%m/%d/%Y",  # 01/15/2024
            "%m-%d-%Y",  # 01-15-2024
            "%d/%m/%Y",  # 15/01/2024
            "%d.%m.%Y",  # 15.01.2024
            "%B %d, %Y",  # January 15, 2024
            "%B %d %Y",  # January 15 2024
            "%b %d, %Y",  # Jan 15, 2024
            "%b %d %Y",  # Jan 15 2024
            "%b. %d, %Y",  # Jan. 15, 2024
            "%b. %d %Y",  # Jan. 15 2024
        ]
    )
    date_patterns: list[str] = Field(
        default_factory=lambda: [
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",  # ISO format: 2024-01-15, 2024/01/15
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",  # US format: 01/15/2024, 1/15/2024
            r"(\d{1,2}[./]\d{1,2}[./]\d{4})",  # European format: 15/01/2024, 15.01.2024
            r"(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",  # Long format: January 15, 2024
            r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})",  # Short format: Jan 15, 2024
        ]
    )


class GranolaConfig(BaseModel):
    """Configuration for Granola link extraction."""

    link_pattern: str = r"Chat with meeting transcript:\s*\[([^\]]+)\]\([^\)]+\)"


class CalendarConfig(BaseModel):
    """Configuration for calendar integration."""

    calendars: dict[str, str] = Field(
        default_factory=lambda: {
            "primary": "primary",
        }
    )
    credentials_path: str = ".obsistant/credentials.json"
    token_path: str = ".obsistant/token.json"


class Config(BaseModel):
    """Main configuration class for obsistant."""

    vault: VaultFoldersConfig = Field(default_factory=VaultFoldersConfig)
    tags: TagsConfig = Field(default_factory=TagsConfig)
    meetings: MeetingsConfig = Field(default_factory=MeetingsConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    granola: GranolaConfig = Field(default_factory=GranolaConfig)
    calendar: CalendarConfig = Field(default_factory=CalendarConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for YAML serialization."""
        return {
            "vault": {
                "folders": {
                    "quick_notes": self.vault.quick_notes,
                    "meetings": self.vault.meetings,
                    "notes": self.vault.notes,
                    "guides": self.vault.guides,
                    "vacations": self.vault.vacations,
                    "files": self.vault.files,
                }
            },
            "tags": {
                "target_tags": self.tags.target_tags,
                "ignored_tags": self.tags.ignored_tags,
                "tag_regex": self.tags.tag_regex,
            },
            "meetings": {
                "filename_format": self.meetings.filename_format,
                "archive_weeks": self.meetings.archive_weeks,
                "auto_tag": self.meetings.auto_tag,
            },
            "processing": {
                "backup_ext": self.processing.backup_ext,
                "date_formats": self.processing.date_formats,
                "date_patterns": self.processing.date_patterns,
            },
            "granola": {
                "link_pattern": self.granola.link_pattern,
            },
            "calendar": {
                "calendars": self.calendar.calendars,
                "credentials_path": self.calendar.credentials_path,
                "token_path": self.calendar.token_path,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create config from dictionary (backward compatibility wrapper).

        This method transforms the YAML structure (with nested "folders" key)
        to match Pydantic model structure and handles backward compatibility.
        """
        # Transform data to match Pydantic model structure
        # Handle vault.folders structure
        vault_data = data.get("vault", {})
        if isinstance(vault_data, dict) and "folders" in vault_data:
            vault_data = vault_data["folders"]

        # Build structure for Pydantic model_validate
        pydantic_data: dict[str, Any] = {}

        if vault_data:
            pydantic_data["vault"] = vault_data

        if "tags" in data:
            pydantic_data["tags"] = data["tags"]

        if "meetings" in data:
            pydantic_data["meetings"] = data["meetings"]

        if "processing" in data:
            pydantic_data["processing"] = data["processing"]

        if "granola" in data:
            pydantic_data["granola"] = data["granola"]

        # Handle calendar section
        calendar_data = data.get("calendar", {})

        if calendar_data:
            pydantic_data["calendar"] = {
                "calendars": calendar_data.get("calendars", {"primary": "primary"}),
                "credentials_path": calendar_data.get(
                    "credentials_path",
                    ".obsistant/credentials.json",
                ),
                "token_path": calendar_data.get(
                    "token_path",
                    ".obsistant/token.json",
                ),
            }

        return cls.model_validate(pydantic_data)

    def to_yaml(self) -> str:
        """Convert config to YAML string."""
        return yaml.safe_dump(self.to_dict(), sort_keys=False, default_flow_style=False)
