import os
from typing import TYPE_CHECKING

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

if TYPE_CHECKING:
    from typing import Any

    agents_config: dict[str, Any]
    tasks_config: dict[str, Any]


@CrewBase
class SummaryCrew:
    """SummaryCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def summary_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config["summary_assistant"],  # type: ignore[attr-defined]
            tools=[],
            llm=os.getenv("MODEL", "gpt-4o-mini"),
            max_rpm=150,
            max_iter=15,
            max_tokens=6000,
            verbose=True,
        )

    @task
    def prepare_summary(self) -> Task:
        return Task(
            config=self.tasks_config["prepare_summary"],  # type: ignore[attr-defined]
            markdown=True,
        )  # type: ignore[call-arg]

    @crew
    def crew(self) -> Crew:
        """Creates the SummaryCrew crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
