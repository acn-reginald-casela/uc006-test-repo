# REFERENCE STUB — validate against current google-adk 2.x docs
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from uc001_requirements_evaluator.config import FLASH_MODEL, EVALUATOR_PROMPT_ID, PRO_MODEL
# from uc001_requirements_evaluator.prompts.evaluator import get_instructions
from uc001_requirements_evaluator.constants import StateKey
from google.adk.planners import BuiltInPlanner
from google.genai import types
from uc001_requirements_evaluator.tools.after_evaluate import stop_loop_if_approved
from uc001_requirements_evaluator.tools.vertex_search import retrieve_clauses
from uc001_requirements_evaluator.tools.prompt_tools import get_prompt

retrieve_clauses_tool = FunctionTool(func=retrieve_clauses)

# Evaluator agent
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
        model=FLASH_MODEL,
        name="evaluator_agent",
        instruction=get_prompt(EVALUATOR_PROMPT_ID),
        description="Scores the requirements against the CRITERIA rubric.",
        output_key = StateKey.EVALUATOR,
        after_agent_callback=stop_loop_if_approved,
        tools = [retrieve_clauses_tool],
        planner = BuiltInPlanner(
            thinking_config = types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget= 1024
            )
        )
    )
