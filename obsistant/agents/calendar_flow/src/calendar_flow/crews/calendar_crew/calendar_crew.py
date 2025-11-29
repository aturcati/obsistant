from typing import TYPE_CHECKING

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from obsistant.agents.calendar_flow.src.calendar_flow.crews.models import (
    CalendarEventsList,
)
from obsistant.agents.calendar_flow.src.calendar_flow.llm_config import (
    create_llm_with_retries,
)
from obsistant.agents.calendar_flow.src.calendar_flow.tools.get_next_week_events_tool import (
    GetNextWeekEvents,
)

if TYPE_CHECKING:
    from typing import Any

    agents_config: dict[str, Any]
    tasks_config: dict[str, Any]


@CrewBase
class CalendarCrew:
    """CalendarCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def calendar_assistant(self) -> Agent:
        llm = create_llm_with_retries(max_completion_tokens=4000)
        return Agent(
            config=self.agents_config["calendar_assistant"],  # type: ignore[attr-defined]
            tools=[GetNextWeekEvents()],
            llm=llm,
            max_rpm=50,  # Limit requests per minute to avoid rate limits
            verbose=True,
        )

    @task
    def get_next_week_events_task(self) -> Task:
        return Task(
            config=self.tasks_config["get_next_week_events_task"],  # type: ignore[attr-defined]
            output_pydantic=CalendarEventsList,
        )  # type: ignore[call-arg]

    @crew
    def crew(self) -> Crew:
        """Creates the OutlookCrew crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
