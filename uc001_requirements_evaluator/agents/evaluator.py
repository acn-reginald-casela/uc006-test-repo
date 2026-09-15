# REFERENCE STUB — validate against current google-adk 2.x docs
from google.adk.agents import Agent

from uc001_requirements_evaluator.config import PRO_MODEL
from uc001_requirements_evaluator.prompts.evaluator import get_instructions
from uc001_requirements_evaluator.constants import StateKey
from uc001_requirements_evaluator.tools.after_evaluate import stop_loop_if_approved

# Data Agent: emits a GENERATION SPEC, never rows. A deterministic engine makes volume.
def build_evaluator_agent() -> Agent:
    """
    Build the Evaluator Agent.

    Model: gemini-pro - scores the test cases against a fixed rubric (see
                       CRITERIA below), one score per criterion, as a JSON
                       array. Its after_agent_callback stops the loop once
                       every criterion scores at/above APPROVAL_SCORE_THRESHOLD.

    Returns:
        Agent ready to be used as the first sub-agent in SequentialAgent.
    """
    return Agent(
        model=PRO_MODEL,
        name="data_agent",
        instruction=get_instructions(),
        description="Scores the test cases against the CRITERIA rubric.",
        output_key = StateKey.EVALUATOR,
        after_agent_callback=stop_loop_if_approved

    )
