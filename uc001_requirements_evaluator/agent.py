# REFERENCE STUB — validate against current google-adk 2.x docs
from google.adk.agents import LoopAgent

from uc001_requirements_evaluator.agents.evaluator import build_evaluator_agent
from uc001_requirements_evaluator.agents.optimizer import build_optimizer_agent

# Sequential pipeline: the Evaluator Agent scores the test cases first, then
# the Optimizer Agent drafts/revises the test cases per that scoring
# feedback.
evaluator = build_evaluator_agent()      # stage 1: evaluate the requirements given
optimizer = build_optimizer_agent()      # stage 2: create a better requirement with the score/feedback given

root_agent = LoopAgent(
name="requirement_refinement_loop",
sub_agents=[evaluator, optimizer],
max_iterations=5
)