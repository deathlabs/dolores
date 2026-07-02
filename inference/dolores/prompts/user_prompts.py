# Standard library imports.
from textwrap import dedent


def get_evaluator_user_prompt(repository: str) -> str:
    """Generates a user prompt for evaluating a repository for security vulnerabilities."""
    return dedent(f"""
        Evaluate the {repository} repository for security vulnerabilities.

        Start by checking your semantic memory and the repository's Pull/Merge Request history. Analyze
        * Successful vulnerability fixes and implementation patterns in merged PRs
        * Unresolved security concerns and rejected approaches in open and closed PRs
        * Patterns in how maintainers respond to security changes

        Clone the repository and evaluates its files for security vulnerabilities.

        For every function and code block, trace where external or untrusted input enters (function arguments, request data, file contents, deserialized data) and follow it to see where it is used. Flag any case where untrusted input reaches a sensitive sink without validation or sanitization, including but not limited to:
        * Hardcoded secrets, credentials, or tokens
        * Insecure or outdated dependencies
        * Injection vulnerabilities, including SQL injection (string-built queries), command injection (shell=True or os.system with unsanitized input), path traversal, and code/template injection
        * Insecure deserialization (pickle, yaml.load, marshal, eval/exec on untrusted data)
        * Insecure authentication or authorization patterns
        * Sensitive data exposure (logging secrets, returning sensitive fields, weak encryption)
        * Misconfigured security controls (debug mode enabled, permissive CORS, disabled TLS verification)

        Do not rely solely on keyword matching. Read each function's logic and identify the vulnerability class even if it does not match a known pattern exactly. Evaluate every file in the repository, including small or seemingly trivial scripts.

        If you find vulnerabilities that require fixes:
        * Create a branch for the fix (e.g., "fix/insecure-deserialization")
        * Check out that branch locally in the cloned repository before editing any files
        * Do not edit or write files until the branch has been checked out locally
        * Edit affected files to apply fixes
        * Verify the local repository is on the correct branch before committing
        * Commit and push your changes with a descriptive message, including a list of vulnerabilities found and fixed
        * Submit a Pull/Merge Request with a detailed description of the vulnerabilities found, the fixes applied, and any relevant context or references

        If no fixes are needed, do not create a branch or push changes.

        Before saving insights, check semantic_memory to see if similar insights already exist. Update or refine existing knowledge instead of creating duplicates.

        Save only actionable, specific insights to semantic memory that will improve future behavior.
    """)
