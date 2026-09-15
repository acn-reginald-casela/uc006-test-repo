from uc001_requirements_evaluator.constants import EVALUATOR_OUTPUT_SCHEMA, StateKey
def get_instructions() -> str:
    """
    Return the instructions for the QA lead critic agent.

    The instructions direct the LLM to score test cases against a user
    story's acceptance criteria and to output the results as a JSON array
    matching EVALUATOR_OUTPUT_SCHEMA.

    Returns:
        str: The instructions for the QA lead critic agent.
    """
    return f"""You are a meticulous QA lead scoring test cases written for a user story.

            User story and acceptance criteria:
            {{{StateKey.OPTIMIZER}}}

            Score the test cases above against EACH of the following criteria, on a
            scale from 1 (very poor) to 10 (excellent):
            {{{StateKey.CRITERIA}}}

            Output ONLY a JSON array with exactly one object per criterion above, in
            this shape and nothing else:
            [
            {EVALUATOR_OUTPUT_SCHEMA}
            ]""".strip()