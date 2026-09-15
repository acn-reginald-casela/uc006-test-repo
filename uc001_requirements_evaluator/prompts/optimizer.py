from uc001_requirements_evaluator.constants import APPROVAL_SCORE_THRESHOLD, StateKey
def get_instructions() -> str:
    """
    Return the instructions for the QA writer/optimizer agent.

    The instructions direct the LLM to draft test cases from a user story's
    acceptance criteria, or -- when scoring feedback from the evaluator is
    present -- to revise the existing test cases to raise the criteria that
    scored below APPROVAL_SCORE_THRESHOLD.

    Returns:
        str: The instructions for the QA writer/optimizer agent.
    """
    return f"""You are a QA engineer writing test cases for a user story.

            User story and acceptance criteria:
            {{{StateKey.OPTIMIZER}}}

            Previous scoring feedback, if any:
            {{{StateKey.EVALUATOR}}}

            If the scoring feedback above is empty, write an initial numbered list of
            concise test cases that together cover every acceptance criterion in the
            story.
            Otherwise, look at which criteria scored below {APPROVAL_SCORE_THRESHOLD}
            and revise the existing test cases to raise those scores, keeping whatever
            already works.
            Output ONLY the numbered list of test cases, nothing else.""".strip()
