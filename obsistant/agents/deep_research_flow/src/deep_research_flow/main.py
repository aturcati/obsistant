#!/usr/bin/env python
from datetime import datetime
from pathlib import Path

from crewai.flow import Flow, listen, router, start
from crewai.flow.persistence import persist
from pydantic import BaseModel

from obsistant.agents.deep_research_flow.src.deep_research_flow.crews.deep_research_crew.crew import (
    DeepResearchCrew,
)
from obsistant.config import load_vault_env
from obsistant.core.frontmatter import render_frontmatter
from obsistant.core.memory_storage import setup_crewai_storage


# define the flow state
class ResearchState(BaseModel):
    user_query: str = ""
    vault_path: str | None = None
    quick_notes_folder: str = "00-Quick Notes"
    needs_research: bool = False
    research_report: str = ""
    final_answer: str = ""


# add persistence to the flow
@persist()
class DeepResearchFlow(Flow[ResearchState]):
    # define the entrypoint
    @start()
    def start_conversation(self):
        """Entry point for the flow"""
        print("🔍 Deep Research Flow started")
        print(f'Query received: "{self.state.user_query}"')

    # define the router - always do research for CLI
    @router(start_conversation)
    def analyze_query(self):
        """Router: Always trigger research for CLI"""
        print("📚 Initiating research process")
        self.state.needs_research = True
        return "RESEARCH"

    # define the clarification task (if research is needed) - skip for CLI
    @router("RESEARCH")
    def clarify_query(self):
        """Skip clarification for CLI - proceed directly to research"""
        print("🔍 Proceeding with research...")

    # define the research execution task
    @router(clarify_query)
    def execute_research(self):
        """Execute the Deep Research Crew"""
        print("🚀 Executing deep research crew...")
        print(f'🔍 Researching: "{self.state.user_query}"')

        # Setup CrewAI storage if vault_path is provided
        if self.state.vault_path:
            setup_crewai_storage(self.state.vault_path, crew_name="deep_research")

        # define the crew
        research_crew = DeepResearchCrew()

        # kickoff the crew with the user query as input
        result = research_crew.crew().kickoff(
            # use the value in the user_query state variable as the input
            inputs={
                "user_query": self.state.user_query,
                "current_year": str(datetime.now().year),
            }
        )

        # update the research_report state variable with the crew's output (use the `raw` attribute)
        self.state.research_report = result.raw

        print("✅ Research completed successfully!")

    # define the task to save and summarize the report
    @router(execute_research)
    def save_report_and_summarize(self):
        """
        Save the final research report to the vault's Quick Notes folder
        """
        if not self.state.vault_path:
            print("❌ No vault path provided, cannot save report")
            self.state.final_answer = self.state.research_report
            return

        vault_path = Path(self.state.vault_path)
        quick_notes_folder = self.state.quick_notes_folder
        quick_notes_dir = vault_path / quick_notes_folder
        quick_notes_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from query (sanitize for filesystem) with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        # Sanitize query for filename: remove special chars, limit length
        sanitized_query = (
            "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_"
                for c in self.state.user_query[:50]
            )
            .strip()
            .replace(" ", "_")
        )
        filename = f"{timestamp}_{sanitized_query}.md"
        output_path = quick_notes_dir / filename

        # Create frontmatter
        frontmatter_data = {
            "created": datetime.now().strftime("%Y-%m-%d"),
            "tags": ["research"],
        }
        frontmatter = render_frontmatter(frontmatter_data)

        # Combine frontmatter and content
        formatted_content = frontmatter + self.state.research_report

        # Save the report
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_content)
            print(f"✅ Report saved successfully to {output_path}")
            self.state.final_answer = (
                f"Research completed and saved to {quick_notes_folder}/{filename}"
            )
        except Exception as e:
            print(f"❌ Failed to save report: {str(e)}")
            self.state.final_answer = self.state.research_report

    # define the final answer task
    @listen("save_report_and_summarize")
    def return_final_answer(self):
        """Return the final answer to the user"""
        print("📝 Final Answer:")
        print(f'📌 Original Query: "{self.state.user_query}"')
        print(f"{self.state.final_answer}")
        print("\n✨ Deep Research Flow completed!")


def kickoff(
    vault_path: Path | str | None = None,
    user_query: str = "",
    quick_notes_folder: str = "00-Quick Notes",
):
    """Kickoff the deep research flow.

    Args:
        vault_path: Path to the Obsidian vault directory (can be Path or str).
        user_query: The research query to investigate.
        quick_notes_folder: Name of the quick notes folder (default: "00-Quick Notes").
    """
    # Load environment variables from .obsistant/.env before creating crews
    if vault_path:
        load_vault_env(vault_path)

    # Instantiate the DeepResearchFlow
    deep_research_flow = DeepResearchFlow()

    # Convert Path to string for CrewAI compatibility
    vault_path_str = str(vault_path) if vault_path else None

    # Kickoff the flow with inputs
    deep_research_flow.kickoff(
        inputs={
            "vault_path": vault_path_str,
            "user_query": user_query,
            "quick_notes_folder": quick_notes_folder,
        }
    )


def plot():
    deep_research_flow = DeepResearchFlow()
    deep_research_flow.plot()


if __name__ == "__main__":
    kickoff()
