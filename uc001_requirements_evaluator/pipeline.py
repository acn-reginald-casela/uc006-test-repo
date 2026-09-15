from google.adk.agents import LoopAgent

from uc001_requirements_evaluator.agents.evaluator import build_evaluator_agent
from uc001_requirements_evaluator.agents.optimizer import build_optimizer_agent

# Sequential pipeline: the Evaluator Agent scores the test cases first, then
# the Optimizer Agent drafts/revises the test cases per that scoring
# feedback.

def build_pipeline() -> LoopAgent:
    """
    Build the full UC001 requirement evaluator.

    # The LoopAgent IS the root agent: runs [evaluator, optimizer] in
    # order, repeatedly. Stops as soon as evaluator's after_agent_callback
    # escalates, or after max_iterations as a safety net if it never approves.
    Returns:
        LoopAgent — the root agent for this system.
    """
    evaluator = build_evaluator_agent()      # stage 1: evaluate the requirements given
    optimizer = build_optimizer_agent()      # stage 2: create a better requirement with the score/feedback given

    return LoopAgent(
    name="requirement_refinement_loop",
    sub_agents=[evaluator, optimizer],
    max_iterations=5
)