# REFERENCE STUB — validate against current google-adk 2.x docs
from google.adk.agents import Agent

from uc001_requirements_evaluator.config import FLASH_MODEL
from uc001_requirements_evaluator.prompts.optimizer import get_instructions
from uc001_requirements_evaluator.constants import StateKey

# Optimizer Agent: drafts test cases from the story, or revises them per the
# evaluator's latest scoring feedback. Runs before the evaluator in the loop.
def build_optimizer_agent() -> Agent:
    """
    Build the Optimizer Agent.

    Model: gemini-flash - on the first pass, drafts test cases straight from
                         the story's requirements/acceptance criteria; on
                         later passes, revises them per the evaluator's
                         scoring feedback.

    Returns:
        Agent ready to be used as a sub-agent in the refinement LoopAgent,
        run before the Evaluator Agent.
    """
    return Agent(
        model=FLASH_MODEL,
        name="optimizer_agent",
        instruction=get_instructions(),
        description="Drafts test cases from the story, or revises them per scoring feedback.",
        output_key=StateKey.OPTIMIZER,
    )
