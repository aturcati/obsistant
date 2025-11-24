"""AI agents integration for obsistant.

This module will contain future crewai-based automation workflows.
"""

from obsistant.agents.calendar_flow.src.calendar_flow.main import (
    kickoff as calendar_kickoff,
)

__all__ = ["calendar_kickoff"]
