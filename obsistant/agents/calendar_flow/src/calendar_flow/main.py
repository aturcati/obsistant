#!/usr/bin/env python
import time
from datetime import datetime
from pathlib import Path

from crewai.flow import Flow, and_, listen, persist, start
from pydantic import BaseModel

from obsistant.agents.calendar_flow.src.calendar_flow.crews.calendar_crew import (
    CalendarCrew,
)
from obsistant.agents.calendar_flow.src.calendar_flow.crews.concert_crew import (
    ConcertCrew,
)
from obsistant.agents.calendar_flow.src.calendar_flow.crews.models import (
    CalendarEventsList,
    ConcertEventsList,
)
from obsistant.agents.calendar_flow.src.calendar_flow.crews.summary_crew import (
    SummaryCrew,
)
from obsistant.core.frontmatter import render_frontmatter
from obsistant.core.memory_storage import setup_crewai_storage


class CalendarState(BaseModel):
    today: str = datetime.now().strftime("%Y-%m-%d")
    vault_path: str | None = None
    meetings_folder: str = "10-Meetings"
    events: CalendarEventsList | None = None
    concerts: ConcertEventsList | None = None
    work_events: CalendarEventsList | None = None
    summary: str = ""


@persist()
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
        if crew_output.pydantic is not None:
            self.state.events = crew_output.pydantic  # type: ignore[assignment]

    @listen(get_next_week_events)
    def research_concerts(self):
        print("Researching concerts")
        if self.state.events is None:
            print("No events found, skipping concert research")
            return

        concerts = [
            e.model_dump() for e in self.state.events.events if e.calendar == "concerts"
        ]

        if not concerts:
            print("No concerts found in events, skipping concert research")
            return

        setup_crewai_storage(self.state.vault_path)

        concert_infos = []
        for i, c in enumerate(concerts):
            print(f"Researching concert {i + 1}/{len(concerts)}")
            concert_result = (
                ConcertCrew()
                .crew()
                .kickoff(
                    inputs={"concert": c, "today": self.state.today},
                )
            )
            concert_infos.append(concert_result.pydantic)

            # Add delay between requests to avoid rate limiting (3 seconds per request)
            if i < len(concerts) - 1:  # Don't delay after the last one
                time.sleep(3)

        self.state.concerts = ConcertEventsList(concerts=concert_infos)

    @listen(get_next_week_events)
    def research_work_events(self):
        print("Researching work events")
        if self.state.events is None:
            print("No events found, skipping work event research")
            return

        work_events = [
            e.model_dump() for e in self.state.events.events if e.calendar == "work"
        ]

        if not work_events:
            print("No work events found in events, skipping work event research")
            return

        self.state.work_events = CalendarEventsList(events=work_events)

    @listen(and_(research_concerts, research_work_events))
    def prepare_summary(self):
        print("Preparing summary")
        # Convert Pydantic models to JSON strings for CrewAI interpolation
        work_events_json = (
            self.state.work_events.model_dump_json() if self.state.work_events else "[]"
        )
        concerts_json = (
            self.state.concerts.model_dump_json() if self.state.concerts else "[]"
        )

        crew_output = (
            SummaryCrew()
            .crew()
            .kickoff(
                inputs={
                    "today": self.state.today,
                    "work_events": work_events_json,
                    "concerts": concerts_json,
                },
            )
        )
        self.state.summary = crew_output.raw

    @listen(prepare_summary)
    def save_summary(self):
        if self.state.vault_path and self.state.meetings_folder:
            vault_path = Path(self.state.vault_path)
            meetings_folder = self.state.meetings_folder
            weekly_summaries_dir = vault_path / meetings_folder / "Weekly Summaries"
            weekly_summaries_dir.mkdir(parents=True, exist_ok=True)
            # Create frontmatter
            frontmatter_data = {
                "created": datetime.now().strftime("%Y-%m-%d"),
                "tags": ["weekly-summary", "meeting"],
            }
            frontmatter = render_frontmatter(frontmatter_data)

            # Combine frontmatter and content
            formatted_content = frontmatter + self.state.summary

            # Save to Weekly Summaries folder with proper filename
            output_filename = "Weekly_Events_Summary.md"
            output_path = weekly_summaries_dir / output_filename

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_content)

            print(f"Summary saved to {output_path}")


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
