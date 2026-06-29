# Standard library imports.
from textwrap import dedent


def get_evaluator_user_prompt(repository: str) -> str:
    """Generates a user prompt for evaluating a repository for security vulnerabilities."""
    return dedent(f"""
        Evaluate the {repository} repository for security vulnerabilities.

        Start by using check_semantic_memory to recall what you already know about {repository}.

        Use list_files to get the full list of files in the repository. Then use read_file to read and evaluate each file for security vulnerabilities. Focus on:
        * Hardcoded secrets, credentials, or tokens
        * Insecure dependencies or outdated packages
        * Injection vulnerabilities (SQL, command, path traversal)
        * Insecure authentication or authorization patterns
        * Sensitive data exposure
        * Misconfigured security controls

        Also use get_pull_requests and get_pull_request_status to understand the PR history. Analyze PRs to identify:
        * Successful vulnerability fixes and implementation patterns in merged PRs
        * Unresolved security concerns and rejected approaches in open and closed PRs
        * Patterns in how maintainers respond to security changes

        If you find vulnerabilities that require fixes:
        * Use git_clone to clone the repository
        * Use git_branch to create a branch
        * Use write_file to apply fixes to affected files
        * Use git_push to commit and push your changes with a descriptive message

        If no fixes are needed, do not create a branch or push changes.

        Before saving insights, check semantic_memory to see if similar insights already exist. Update or refine existing knowledge instead of creating duplicates.

        Use update_semantic_memory to save only actionable, specific insights that will improve future behavior.
    """)
