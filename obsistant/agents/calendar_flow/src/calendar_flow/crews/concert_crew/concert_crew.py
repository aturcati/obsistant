import os
from typing import TYPE_CHECKING

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import EXASearchTool, ScrapeWebsiteTool, TavilySearchTool
from dotenv import find_dotenv, load_dotenv

from obsistant.agents.calendar_flow.src.calendar_flow.crews.models import (
    ConcertEvent,
)

load_dotenv(find_dotenv())

if TYPE_CHECKING:
    from typing import Any

    agents_config: dict[str, Any]
    tasks_config: dict[str, Any]


@CrewBase
class ConcertCrew:
    """ConcertCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def research_planner(self) -> Agent:
        return Agent(
            config=self.agents_config["research_planner"],  # type: ignore[attr-defined]
            tools=[],
            llm=os.getenv("MODEL", "gpt-4o-mini"),
            max_rpm=150,
            max_iter=15,
            max_tokens=6000,
            verbose=True,
        )

    @agent
    def concert_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["concert_researcher"],  # type: ignore[attr-defined]
            tools=[ScrapeWebsiteTool(), EXASearchTool(), TavilySearchTool()],
            llm=os.getenv("MODEL", "gpt-4o-mini"),
            max_rpm=150,
            max_iter=15,
            max_tokens=6000,
            verbose=True,
        )

    @agent
    def concert_factchecker(self) -> Agent:
        return Agent(
            config=self.agents_config["concert_factchecker"],  # type: ignore[attr-defined]
            tools=[EXASearchTool()],
            llm=os.getenv("MODEL", "gpt-4o-mini"),
            max_rpm=150,
            max_iter=15,
            max_tokens=6000,
            verbose=True,
        )

    @agent
    def concert_summary_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config["concert_summary_assistant"],  # type: ignore[attr-defined]
            tools=[],
            llm=os.getenv("MODEL", "gpt-4o-mini"),
            max_rpm=150,
            max_iter=15,
            max_tokens=6000,
            verbose=True,
        )

    @task
    def create_research_plan(self) -> Task:
        return Task(
            config=self.tasks_config["create_research_plan"]  # type: ignore[attr-defined]
        )  # type: ignore[call-arg]

    @task
    def research_concert_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_concert_task"]  # type: ignore[attr-defined]
        )  # type: ignore[call-arg]

    @task
    def concert_factcheck_task(self) -> Task:
        return Task(
            config=self.tasks_config["concert_factcheck_task"]  # type: ignore[attr-defined]
        )  # type: ignore[call-arg]

    @task
    def concert_research_summary(self) -> Task:
        return Task(
            config=self.tasks_config["concert_research_summary"],  # type: ignore[attr-defined]
            output_pydantic=ConcertEvent,
        )  # type: ignore[call-arg]

    @crew
    def crew(self) -> Crew:
        """Creates the ConcertCrew crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            verbose=True,
        )
