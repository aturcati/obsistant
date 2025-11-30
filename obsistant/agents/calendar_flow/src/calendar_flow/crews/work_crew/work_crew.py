import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import (
    TextFileKnowledgeSource,
)
from crewai.project import CrewBase, agent, crew, task
from crewai_tools.tools.qdrant_vector_search_tool.qdrant_search_tool import (
    QdrantConfig,
)
from qdrant_client.http import models as qmodels

from obsistant.agents.calendar_flow.src.calendar_flow.crews.models import (
    WorkEvent,
)
from obsistant.agents.calendar_flow.src.calendar_flow.llm_config import (
    create_llm_with_retries,
)
from obsistant.agents.calendar_flow.src.calendar_flow.tools.qdrant_search_tool import (
    OverloadQdrantTool,
)

if TYPE_CHECKING:
    from typing import Any

    agents_config: dict[str, Any]
    tasks_config: dict[str, Any]


@CrewBase
class WorkCrew:
    """WorkCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    def _create_qdrant_tool(self, filter: qmodels.Filter) -> OverloadQdrantTool:
        """Create and configure the Qdrant search tool."""
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        collection_name = os.getenv("QDRANT_COLLECTION", "work")

        return OverloadQdrantTool(
            qdrant_config=QdrantConfig(
                qdrant_url=qdrant_url,
                collection_name=collection_name,
                limit=5,
                score_threshold=0.4,
                filter=filter,
            )
        )

    @agent
    def search_agent(self) -> Agent:
        llm = create_llm_with_retries(max_completion_tokens=4000)
        # Filter for past meetings
        filter_past_meetings = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="created",
                    range=qmodels.DatetimeRange(
                        gte=datetime.now() - timedelta(days=14)
                    ),
                ),
            ]
        )
        qdrant_tool = self._create_qdrant_tool(filter_past_meetings)
        return Agent(
            config=self.agents_config["search_agent"],  # type: ignore[attr-defined]
            tools=[qdrant_tool],
            llm=llm,
            max_rpm=50,
            max_iter=5,
            verbose=True,
        )

    @agent
    def past_meetings_summarizer_agent(self) -> Agent:
        llm = create_llm_with_retries(max_completion_tokens=4000)
        return Agent(
            config=self.agents_config["past_meetings_summarizer_agent"],  # type: ignore[attr-defined]
            tools=[],
            llm=llm,
            max_rpm=50,
            max_iter=5,
            verbose=True,
        )

    @agent
    def summary_structure_assistant(self) -> Agent:
        llm = create_llm_with_retries(max_completion_tokens=4000)
        return Agent(
            config=self.agents_config["summary_structure_assistant"],  # type: ignore[attr-defined]
            tools=[],
            llm=llm,
            max_rpm=50,
            max_iter=5,
            verbose=True,
        )

    @task
    def search_past_meetings_task(self) -> Task:
        return Task(
            config=self.tasks_config["search_past_meetings_task"]  # type: ignore[attr-defined]
        )  # type: ignore[call-arg]

    @task
    def summarize_past_meetings_task(self) -> Task:
        return Task(
            config=self.tasks_config["summarize_past_meetings_task"]  # type: ignore[attr-defined]
        )  # type: ignore[call-arg]

    @task
    def structure_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config["structure_summary_task"],  # type: ignore[attr-defined]
            output_pydantic=WorkEvent,
        )  # type: ignore[call-arg]

    def _get_knowledge_sources(self) -> list[BaseKnowledgeSource]:
        """Get knowledge sources for the work crew.

        CrewAI's TextFileKnowledgeSource expects files in a 'knowledge' directory
        relative to the current working directory. The working directory is set
        to the storage directory before crew creation, so CrewAI can find the files.
        """
        # Check if knowledge file exists relative to current working directory
        # (which should be set to storage_dir before crew creation)
        knowledge_file = Path("knowledge") / "user_preference.md"
        if knowledge_file.exists():
            # CrewAI prepends 'knowledge/' to paths, so we provide just the filename
            return [TextFileKnowledgeSource(file_paths=["user_preference.md"])]
        return []

    @crew
    def crew(self) -> Crew:
        """Creates the WorkCrew crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            knowledge_sources=self._get_knowledge_sources(),
            verbose=True,
        )
