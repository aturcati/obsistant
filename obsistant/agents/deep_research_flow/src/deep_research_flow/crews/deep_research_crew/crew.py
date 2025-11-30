from typing import TYPE_CHECKING

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import EXASearchTool, ScrapeWebsiteTool

from obsistant.agents.calendar_flow.src.calendar_flow.llm_config import (
    create_llm_with_retries,
)
from obsistant.agents.deep_research_flow.src.deep_research_flow.crews.deep_research_crew.guardrails.guardrails import (
    write_report_guardrail,
)

if TYPE_CHECKING:
    from typing import Any

    agents_config: dict[str, Any]
    tasks_config: dict[str, Any]


@CrewBase
class DeepResearchCrew:
    """DeepResearch crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # Define the agents
    @agent
    def research_planner(self) -> Agent:
        return Agent(
            config=self.agents_config["research_planner"],  # type: ignore[attr-defined]
            llm=create_llm_with_retries(),
            verbose=True,
        )

    @agent
    def topic_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["topic_researcher"],  # type: ignore[attr-defined]
            tools=[
                EXASearchTool(),
                ScrapeWebsiteTool(),
            ],
            llm=create_llm_with_retries(),
            verbose=True,
            max_rpm=150,
            max_iter=15,
        )

    @agent
    def fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config["fact_checker"],  # type: ignore[attr-defined]
            tools=[
                EXASearchTool(),
                ScrapeWebsiteTool(),
            ],
            llm=create_llm_with_retries(),
            verbose=True,
            max_rpm=150,
            max_iter=15,
        )

    @agent
    def report_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["report_writer"],  # type: ignore[attr-defined]
            llm=create_llm_with_retries(),
            verbose=True,
            max_rpm=150,
            max_iter=15,
        )

    @task
    def create_research_plan(self) -> Task:
        return Task(
            config=self.tasks_config["create_research_plan"],  # type: ignore[attr-defined]
        )  # type: ignore[call-arg]

    # Define the tasks
    @task
    def research_main_topics(self) -> Task:
        return Task(
            config=self.tasks_config["research_main_topics"],  # type: ignore[attr-defined]
            async_execution=True,
        )  # type: ignore[call-arg]

    @task
    def research_secondary_topics(self) -> Task:
        return Task(
            config=self.tasks_config["research_secondary_topics"],  # type: ignore[attr-defined]
            async_execution=True,
        )  # type: ignore[call-arg]

    @task
    def validate_main_topics(self) -> Task:
        return Task(
            config=self.tasks_config["validate_main_topics"],  # type: ignore[attr-defined]
        )  # type: ignore[call-arg]

    @task
    def validate_secondary_topics(self) -> Task:
        return Task(
            config=self.tasks_config["validate_secondary_topics"],  # type: ignore[attr-defined]
        )  # type: ignore[call-arg]

    @task
    def write_final_report(self) -> Task:
        return Task(
            config=self.tasks_config["write_final_report"],  # type: ignore[attr-defined]
            guardrails=[write_report_guardrail],
            markdown_output=True,  # type: ignore[arg-type]
            output_file="final_report.md",
        )  # type: ignore[call-arg]

    # Define the crew
    @crew
    def crew(self) -> Crew:
        """Creates the ParallelDeepResearchCrew crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            memory=True,
            process=Process.sequential,
            tracing=True,
            verbose=True,
        )
