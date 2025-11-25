"""Configuration schema for obsistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class VaultFoldersConfig:
    """Configuration for vault folder names."""

    quick_notes: str = "00-Quick Notes"
    meetings: str = "10-Meetings"
    notes: str = "20-Notes"
    guides: str = "30-Guides"
    vacations: str = "40-Vacations"
    files: str = "50-Files"


@dataclass
class TagsConfig:
    """Configuration for tag processing."""

    target_tags: list[str] = field(
        default_factory=lambda: [
            "products",
            "projects",
            "devops",
            "challenges",
            "events",
        ]
    )
    ignored_tags: list[str] = field(default_factory=lambda: ["olt"])
    tag_regex: str = r"(?<!\w)#([\w/-]+)(?=\s|$)"


@dataclass
class MeetingsConfig:
    """Configuration for meeting processing."""

    filename_format: str = "YYMMDD_Title"
    archive_weeks: int = 2
    auto_tag: str = "meeting"


@dataclass
class ProcessingConfig:
    """Configuration for general processing."""

    backup_ext: str = ".bak"
    date_formats: list[str] = field(
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
    date_patterns: list[str] = field(
        default_factory=lambda: [
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",  # ISO format: 2024-01-15, 2024/01/15
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",  # US format: 01/15/2024, 1/15/2024
            r"(\d{1,2}[./]\d{1,2}[./]\d{4})",  # European format: 15/01/2024, 15.01.2024
            r"(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",  # Long format: January 15, 2024
            r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})",  # Short format: Jan 15, 2024
        ]
    )


@dataclass
class GranolaConfig:
    """Configuration for Granola link extraction."""

    link_pattern: str = r"Chat with meeting transcript:\s*\[([^\]]+)\]\([^\)]+\)"


@dataclass
class CalendarConfig:
    """Configuration for calendar integration."""

    calendars: dict[str, str] = field(
        default_factory=lambda: {
            "primary": "primary",
        }
    )


@dataclass
class Config:
    """Main configuration class for obsistant."""

    vault: VaultFoldersConfig = field(default_factory=VaultFoldersConfig)
    tags: TagsConfig = field(default_factory=TagsConfig)
    meetings: MeetingsConfig = field(default_factory=MeetingsConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    granola: GranolaConfig = field(default_factory=GranolaConfig)
    calendar: CalendarConfig = field(default_factory=CalendarConfig)

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
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create config from dictionary."""
        vault_data = data.get("vault", {}).get("folders", {})
        tags_data = data.get("tags", {})
        meetings_data = data.get("meetings", {})
        processing_data = data.get("processing", {})
        granola_data = data.get("granola", {})
        calendar_data = data.get("calendar", {})

        return cls(
            vault=VaultFoldersConfig(
                quick_notes=vault_data.get("quick_notes", "00-Quick Notes"),
                meetings=vault_data.get("meetings", "10-Meetings"),
                notes=vault_data.get("notes", "20-Notes"),
                guides=vault_data.get("guides", "30-Guides"),
                vacations=vault_data.get("vacations", "40-Vacations"),
                files=vault_data.get("files", "50-Files"),
            ),
            tags=TagsConfig(
                target_tags=tags_data.get(
                    "target_tags",
                    ["products", "projects", "devops", "challenges", "events"],
                ),
                ignored_tags=tags_data.get("ignored_tags", ["olt"]),
                tag_regex=tags_data.get("tag_regex", r"(?<!\w)#([\w/-]+)(?=\s|$)"),
            ),
            meetings=MeetingsConfig(
                filename_format=meetings_data.get("filename_format", "YYMMDD_Title"),
                archive_weeks=meetings_data.get("archive_weeks", 2),
                auto_tag=meetings_data.get("auto_tag", "meeting"),
            ),
            processing=ProcessingConfig(
                backup_ext=processing_data.get("backup_ext", ".bak"),
                date_formats=processing_data.get(
                    "date_formats",
                    [
                        "%Y-%m-%d",
                        "%Y/%m/%d",
                        "%m/%d/%Y",
                        "%m-%d-%Y",
                        "%d/%m/%Y",
                        "%d.%m.%Y",
                        "%B %d, %Y",
                        "%B %d %Y",
                        "%b %d, %Y",
                        "%b %d %Y",
                        "%b. %d, %Y",
                        "%b. %d %Y",
                    ],
                ),
                date_patterns=processing_data.get(
                    "date_patterns",
                    [
                        r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
                        r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
                        r"(\d{1,2}[./]\d{1,2}[./]\d{4})",
                        r"(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",
                        r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})",
                    ],
                ),
            ),
            granola=GranolaConfig(
                link_pattern=granola_data.get(
                    "link_pattern",
                    r"Chat with meeting transcript:\s*\[([^\]]+)\]\([^\)]+\)",
                ),
            ),
            calendar=CalendarConfig(
                calendars=calendar_data.get(
                    "calendars",
                    {"primary": "primary"},
                ),
            ),
        )

    def to_yaml(self) -> str:
        """Convert config to YAML string."""
        return yaml.safe_dump(self.to_dict(), sort_keys=False, default_flow_style=False)
