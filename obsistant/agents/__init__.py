"""AI agents integration for obsistant.

This module will contain future crewai-based automation workflows.
"""

from obsistant.agents.calendar_flow.src.calendar_flow.main import (
    kickoff as calendar_kickoff,
)
from obsistant.agents.deep_research_flow.src.deep_research_flow.main import (
    kickoff as deep_research_kickoff,
)

__all__ = ["calendar_kickoff", "deep_research_kickoff"]
