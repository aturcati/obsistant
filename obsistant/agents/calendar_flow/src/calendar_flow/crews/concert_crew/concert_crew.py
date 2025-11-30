from typing import TYPE_CHECKING

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import EXASearchTool, ScrapeWebsiteTool, TavilySearchTool

from obsistant.agents.calendar_flow.src.calendar_flow.crews.models import (
    ConcertEvent,
)
from obsistant.agents.calendar_flow.src.calendar_flow.llm_config import (
    create_llm_with_retries,
)

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
        llm = create_llm_with_retries(max_completion_tokens=4000)
        return Agent(
            config=self.agents_config["research_planner"],  # type: ignore[attr-defined]
            tools=[],
            llm=llm,
            max_rpm=50,  # Reduced to avoid rate limits
            max_iter=5,  # Reduced iterations to limit token usage
            verbose=True,
        )

    @agent
    def concert_researcher(self) -> Agent:
        llm = create_llm_with_retries(max_completion_tokens=4000)
        return Agent(
            config=self.agents_config["concert_researcher"],  # type: ignore[attr-defined]
            tools=[ScrapeWebsiteTool(), EXASearchTool(), TavilySearchTool()],
            llm=llm,
            max_rpm=50,  # Reduced to avoid rate limits
            max_iter=8,  # Reduced iterations to limit token usage
            verbose=True,
        )

    @agent
    def concert_factchecker(self) -> Agent:
        llm = create_llm_with_retries(max_completion_tokens=4000)
        return Agent(
            config=self.agents_config["concert_factchecker"],  # type: ignore[attr-defined]
            tools=[EXASearchTool()],
            llm=llm,
            max_rpm=50,  # Reduced to avoid rate limits
            max_iter=5,  # Reduced iterations to limit token usage
            verbose=True,
        )

    @agent
    def concert_summary_assistant(self) -> Agent:
        llm = create_llm_with_retries(max_completion_tokens=4000)
        return Agent(
            config=self.agents_config["concert_summary_assistant"],  # type: ignore[attr-defined]
            tools=[],
            llm=llm,
            max_rpm=50,  # Reduced to avoid rate limits
            max_iter=5,  # Reduced iterations to limit token usage
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
