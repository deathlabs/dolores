# Standard library imports.
from textwrap import dedent


def get_user_prompt(repository: str) -> str:
    """Generate a user prompt for evaluating a repository for security vulnerabilities."""
    return dedent(f"""
        Evaluate the {repository} repository for security vulnerabilities and follow your standard loop.

        Step 1: Recall memory
        Check semantic memory for any prior facts, conventions, or lessons learned about this repository, and check procedural memory for any coding conventions or style instructions, before doing anything else.

        Step 2: Review your prior pull requests
        Review every pull request you have previously submitted to this repository.

        For open PRs: review unresolved comments and requested changes on every open PR you have previously submitted.

        For each comment, decide whether it is:
        * Security or acceptance relevant: this is actionable, you will push a fix to the existing branch in step 4.
        * A style, formatting, or convention preference: derive a concrete, generalizable instruction from it. This is actionable, you will save it to procedural memory in step 3 and apply it in step 4.
        * Actionable but unclear: the comment asks for something you don't have enough context to act on safely. Reply to the comment acknowledging it and asking for the specific clarification you need. Do not fix, do not guess. Save a note to semantic memory that this comment is awaiting clarification, and check on future runs whether an answer has been given before treating it as unresolved again.
        * Neither of the above (a one-off, non-generalizable opinion): not actionable. Do not comment or push anything, and do not save it to procedural memory.

        If a comment is purely an acknowledgment opportunity, for example a reviewer confirmed your fix looks correct or your interpretation of a prior clarification was right, reply with a brief acknowledgment. This is not a fix and does not require a code change.

        For closed, unmerged PRs: check whether semantic memory already explains why each one was rejected. If it does not, extract the reason from the available evidence and save it now.

        Step 3: Update memory
        Persist everything you concluded in step 2 to the correct memory type. Facts about this repository, its vulnerabilities, and its PR status go to semantic memory. Generalizable instructions for how to write or format code go to procedural memory. A conclusion you only describe in your response but do not save has not actually updated your knowledge. Check for existing related entries first in the appropriate memory type and refine them rather than creating duplicates.

        Step 4: Fix actionable issues on your open PRs
        For every open PR you flagged as actionable (security/acceptance relevant or style/convention) in step 2, check out its existing branch now, before doing anything else in this step. Apply the fix directly:
        * For a security or acceptance relevant comment, fix the underlying issue.
        * For a style or convention preference, check whether the code currently on that branch violates the procedural memory instruction you just saved. If it does, fix it there, not just in future code you write later.
        Push the fix to the existing branch. Do not leave a new comment about the fix itself, pushing the commit is sufficient. Any acknowledgment or clarification replies from step 2 should already have been sent in that step, not here. A fix you only reasoned about but did not write and push is not complete, do not move to step 5 until the fix has actually been pushed.

        Step 5: Clone or update and evaluate the repository
        Clone or update the repository and evaluate every file for security vulnerabilities. For every function and code block, trace where external or untrusted input enters (function arguments, request data, file contents, deserialized data) and follow it to where it is used. Flag any case where untrusted input reaches a sensitive sink without validation or sanitization, including but not limited to hardcoded secrets, insecure or outdated dependencies, injection vulnerabilities, insecure deserialization, insecure authentication or authorization, sensitive data exposure, and misconfigured security controls. Do not rely solely on keyword matching, and do not skip small or trivial files.

        Step 6: Check for existing coverage
        For each vulnerability found, check whether an existing branch or open PR already addresses it. Do not duplicate a fix already in progress.

        Step 7: Create a branch and apply the fix
        For vulnerabilities not already covered, create a branch with a descriptive name (e.g., "fix/insecure-deserialization") and apply the fix. Verify you are on the correct branch before committing. Commit with a message that lists the vulnerabilities found and fixed.

        Step 8: Submit a PR if necessary
        Submit a pull request only for a newly created branch from step 7 that addresses a vulnerability not already covered by an existing PR. Include a description of the vulnerabilities found, the fixes applied, and relevant context. If no fixes were needed, or everything was already covered, do not submit a PR.

        Before finishing, confirm every decision and insight from this run has actually been saved to the correct memory, every fix you decided on has actually been written and pushed, and every acknowledgment or clarification you decided on has actually been sent as a reply, not just stated in your response.
    """)
