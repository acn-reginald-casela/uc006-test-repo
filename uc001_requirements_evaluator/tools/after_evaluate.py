import json
from uc001_requirements_evaluator.constants import StateKey, APPROVAL_SCORE_THRESHOLD
from google.adk.agents.callback_context import CallbackContext
from uc001_requirements_evaluator.tools.formatter import clean_json_string
def stop_loop_if_approved(callback_context: CallbackContext):
    """after_agent_callback on CriticAgent: escalate once every criterion is approved.

    `CallbackContext.actions` is the same `EventActions` object a tool would
    get from `ToolContext.actions`. By the time this callback runs, the
    critic's `output_key` write (the JSON scores array) has already landed
    in state, so we can just parse it and decide whether to stop the loop --
    no tool call, and no extra LLM turn, needed.
    """
    # try:
    # print(callback_context.state.get(StateKey.EVALUATOR, ""))
    scores = clean_json_string(callback_context.state.get(StateKey.EVALUATOR, ""))
    if isinstance(scores, str):
        try:
            scores = json.loads(scores)
        except Exception:
            print("cant convert to json/dict")

    iteration = callback_context.state.get(StateKey.ITERATION, 0) + 1
    callback_context.state[StateKey.ITERATION] = iteration
    print(f"  [callback] {callback_context.agent_name} iteration {iteration}")

    min_score = min(entry.get("score", 0) for entry in scores)
    version = {"text": callback_context.state.get(StateKey.OPTIMIZER), "min": min_score}

    best = callback_context.state.get("best_version")
    if best is None or version["min"] > best["min"]:
        callback_context.state["best_version"] = version           # keep the best, not the last

    if min_score >= APPROVAL_SCORE_THRESHOLD:
        print(f"  [callback] {callback_context.agent_name} approved at iteration {iteration} (all scores >= {APPROVAL_SCORE_THRESHOLD}) -> stopping loop")
        callback_context.state["converged"] = True
        callback_context.actions.escalate = True