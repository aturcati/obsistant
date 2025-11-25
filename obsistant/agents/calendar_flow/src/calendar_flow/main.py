#!/usr/bin/env python
import os
from datetime import datetime
from pathlib import Path

from crewai.flow import Flow, listen, start
from pydantic import BaseModel

from obsistant.agents.calendar_flow.src.calendar_flow.crews.calendar_crew.calendar_crew import (
    CalendarCrew,
)
from obsistant.core.frontmatter import render_frontmatter


class CalendarState(BaseModel):
    today: str = datetime.now().strftime("%Y-%m-%d")
    summary: str = ""
    vault_path: str | None = None
    meetings_folder: str = "10-Meetings"


class CalendarFlow(Flow[CalendarState]):
    @start()
    def get_next_week_events(self):
        print("Getting next week events")
        crew_output = (
            CalendarCrew()
            .crew()
            .kickoff(
                inputs={"today": self.state.today, "vault_path": self.state.vault_path}
            )
        )
        self.state.summary = crew_output.raw if crew_output.raw else ""

    @listen(get_next_week_events)
    def save_summary(self):
        if not os.path.exists("weekly_events_summary.md"):
            print("Weekly events summary file does not exist")
            return

        # Read the generated summary
        with open("weekly_events_summary.md", encoding="utf-8") as f:
            content = f.read()

        # If vault_path is provided, organize the file properly
        if self.state.vault_path and self.state.meetings_folder:
            vault_path = Path(self.state.vault_path)
            meetings_folder = self.state.meetings_folder

            # Create Weekly Summaries folder
            weekly_summaries_dir = vault_path / meetings_folder / "Weekly Summaries"
            weekly_summaries_dir.mkdir(parents=True, exist_ok=True)

            # Calculate week number (1-52/53) from current date
            today = datetime.now()
            # Calculate week number from January 1st
            jan_1 = datetime(today.year, 1, 1)
            days_since_jan_1 = (today - jan_1).days
            week_number = (days_since_jan_1 // 7) + 1

            # Create frontmatter
            frontmatter_data = {
                "created": today.strftime("%Y-%m-%d"),
                "tags": ["weekly-summary", "meeting"],
            }
            frontmatter = render_frontmatter(frontmatter_data)

            # Combine frontmatter and content
            formatted_content = frontmatter + content

            # Save to Weekly Summaries folder with proper filename
            output_filename = f"Weekly_Meeting_Summary_{week_number}.md"
            output_path = weekly_summaries_dir / output_filename

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_content)

            print(f"Summary saved to {output_path}")

            # Clean up temporary file
            os.remove("weekly_events_summary.md")
        else:
            # Fallback: just read the file into state
            self.state.summary = content


def kickoff(vault_path: Path | str | None = None, meetings_folder: str = "10-Meetings"):
    """Kickoff the calendar flow.

    Args:
        vault_path: Path to the Obsidian vault directory (can be Path or str).
        meetings_folder: Name of the meetings folder (default: "10-Meetings").
    """
    calendar_flow = CalendarFlow()
    # Convert Path to string for CrewAI compatibility
    vault_path_str = str(vault_path) if vault_path else None
    calendar_flow.kickoff(
        inputs={"vault_path": vault_path_str, "meetings_folder": meetings_folder}
    )


def plot():
    calendar_flow = CalendarFlow()
    calendar_flow.plot()


if __name__ == "__main__":
    kickoff()
