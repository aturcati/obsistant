#!/usr/bin/env python
import json
import sys
from datetime import datetime

from obsistant.agents.deep_research_flow.src.deep_research_flow.crews.deep_research_crew.crew import (
    DeepResearchCrew,
)


def run():
    """
    Run the crew.
    """
    inputs = {
        "user_query": "Quantum Computing",
        "current_year": str(datetime.now().year),
    }

    try:
        DeepResearchCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}") from e


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "user_query": "Quantum Computing",
        "current_year": str(datetime.now().year),
    }
    try:
        DeepResearchCrew().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}") from e


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        DeepResearchCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}") from e


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "user_query": "Quantum Computing",
        "current_year": str(datetime.now().year),
    }

    try:
        DeepResearchCrew().crew().test(
            n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}") from e


def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    if len(sys.argv) < 2:
        raise Exception(
            "No trigger payload provided. Please provide JSON payload as argument."
        )

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        raise Exception("Invalid JSON payload provided as argument") from e

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "user_query": "",
        "current_year": "",
    }

    try:
        result = DeepResearchCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(
            f"An error occurred while running the crew with trigger: {e}"
        ) from e
