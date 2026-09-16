from uc001_requirements_evaluator.constants import APPROVAL_SCORE_THRESHOLD, StateKey
def get_instructions() -> str:
    """
    Return the instructions for the QA writer/optimizer agent.

    The instructions direct the LLM to draft requirements from a user story's
    acceptance criteria, or -- when scoring feedback from the evaluator is
    present -- to revise the existing requirements to raise the criteria that
    scored below APPROVAL_SCORE_THRESHOLD.

    Returns:
        str: The instructions for the QA writer/optimizer agent.
    """
    return f"""You are a QA engineer writing requirements for a user story.

            User story and acceptance criteria:
            {{{StateKey.OPTIMIZER}}}

            Previous scoring feedback, if any:
            {{{StateKey.EVALUATOR}}}

            If the scoring feedback above is empty, write an initial numbered list of
            concise requirements that together cover every acceptance criterion in the
            story.
            Otherwise, look at which criteria scored below {APPROVAL_SCORE_THRESHOLD}
            and revise the existing requirements to raise those scores, keeping whatever
            already works. 
            
            PRESERVE the author's intent — improve expression, structure, and testability.
            If a defect needs a business decision you do not have (a missing rule, an external unknown),
            do NOT invent it: record it under OPEN_QUESTIONS for the author
            
            Output ONLY the numbered list of requirements, nothing else.""".strip()
