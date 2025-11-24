from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from dotenv import find_dotenv, load_dotenv

from obsistant.agents.calendar_flow.src.calendar_flow.tools.get_next_week_events_tool import (
    GetNextWeekEvents,
)

load_dotenv(find_dotenv())

get_next_week_events_tool = GetNextWeekEvents()


@CrewBase
class CalendarCrew:
    """CalendarCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def calendar_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config["calendar_assistant"],  # type: ignore[index]
            tools=[get_next_week_events_tool],
            verbose=True,
        )

    @agent
    def event_summary_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config["event_summary_assistant"],  # type: ignore[index]
            verbose=True,
        )

    @task
    def get_next_week_events_task(self) -> Task:
        task_config = self.tasks_config["get_next_week_events_task"]  # type: ignore[index]
        return Task(
            **task_config,
            agent=self.calendar_assistant(),
        )

    @task
    def summarize_events_task(self) -> Task:
        task_config = self.tasks_config["summarize_events_task"]  # type: ignore[index]
        return Task(
            **task_config,
            agent=self.event_summary_assistant(),
            output_file="weekly_events_summary.md",
        )

    @crew
    def crew(self) -> Crew:
        """Creates the OutlookCrew crew"""

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
