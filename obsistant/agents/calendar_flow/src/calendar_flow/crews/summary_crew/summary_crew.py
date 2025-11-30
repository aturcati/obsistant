import re
from typing import TYPE_CHECKING

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, after_kickoff, agent, crew, task

from obsistant.agents.calendar_flow.src.calendar_flow.llm_config import (
    create_llm_with_retries,
)

if TYPE_CHECKING:
    from typing import Any

    agents_config: dict[str, Any]
    tasks_config: dict[str, Any]


def strip_markdown_wrapper(text: str) -> str:
    text = text.strip()
    # Remove opening ```markdown (only at start)
    text = re.sub(r"^```markdown\s*\n?", "", text, flags=re.IGNORECASE)
    # Remove closing ``` (only at end)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


@CrewBase
class SummaryCrew:
    """SummaryCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def summary_assistant(self) -> Agent:
        llm = create_llm_with_retries(
            model="gpt-5", max_completion_tokens=4000, temperature=0.0
        )
        return Agent(
            config=self.agents_config["summary_assistant"],  # type: ignore[attr-defined]
            tools=[],
            llm=llm,
            max_rpm=30,  # Reduced to avoid rate limits (TPM: 30,000 limit)
            max_iter=5,  # Reduced iterations to limit token usage
            verbose=True,
        )

    @task
    def prepare_summary(self) -> Task:
        return Task(
            config=self.tasks_config["prepare_summary"],  # type: ignore[attr-defined]
            markdown=True,
        )  # type: ignore[call-arg]

    @after_kickoff
    def strip_markdown(self, result):
        try:
            summary = result if type(result) == str else result.raw  # noqa: E721
            summary = strip_markdown_wrapper(summary)
            result.raw = summary
        except Exception as e:
            print(f"Error stripping markdown: {e}")
        return result

    @crew
    def crew(self) -> Crew:
        """Creates the SummaryCrew crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
