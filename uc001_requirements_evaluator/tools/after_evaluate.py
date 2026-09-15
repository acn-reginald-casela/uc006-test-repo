import json
from uc001_requirements_evaluator.constants import StateKey, APPROVAL_SCORE_THRESHOLD
from google.adk.agents.callback_context import CallbackContext
def stop_loop_if_approved(callback_context: CallbackContext):
    """after_agent_callback on CriticAgent: escalate once every criterion is approved.

    `CallbackContext.actions` is the same `EventActions` object a tool would
    get from `ToolContext.actions`. By the time this callback runs, the
    critic's `output_key` write (the JSON scores array) has already landed
    in state, so we can just parse it and decide whether to stop the loop --
    no tool call, and no extra LLM turn, needed.
    """
    try:
        scores = json.loads(callback_context.state.get(StateKey.EVALUATOR, ""))
    except (TypeError, ValueError):
        return  # critic didn't return valid JSON this pass; let the writer try again

    if scores and all(entry.get("score", 0) >= APPROVAL_SCORE_THRESHOLD for entry in scores):
        print(f"  [callback] {callback_context.agent_name} approved (all scores >= {APPROVAL_SCORE_THRESHOLD}) -> stopping loop")
        callback_context.actions.escalate = True