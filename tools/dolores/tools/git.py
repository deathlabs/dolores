# Standard library imports.
from pathlib import Path
from os import getenv

# Third party imports.
from git import InvalidGitRepositoryError, Repo
from fastmcp.tools import tool

# Local imports.
from dolores.config import DOWNLOADS_DIR


@tool(description="Clones a Git repository.")
async def clone_git_repository(url: str, repo_name: str) -> None | str:
    """Clone a Git repository.

    Args:
        url: The URL of the Git repository to clone.
        repo_name: The name of the repository to clone.

    Returns:
        The path to the cloned repository if successful, or an error message if failed.
    """

    # Define where to clone the repository.
    to_path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    # Check if the repository has already been cloned.
    if not to_path.exists():
        try:
            Repo.clone_from(url=url, to_path=to_path)
        except Exception as error:
            return f"Failed to clone the {repo_name} repository: {error}"

    return to_path.resolve()


@tool(
    description="Checks out a branch in a cloned repository, creating it locally if needed."
)
async def checkout_git_branch(repo_name: str, branch: str, base_branch: str) -> str:
    """Check out a branch in a cloned Git repository.

    Args:
        repo_name: The name of the repository (e.g., "username/repo").
        branch: The branch to check out.
        base_branch: The branch to base a new local branch on if it doesn't exist yet.

    Returns:
        A message if successful, or an error message if failed.
    """
    to_path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    if not to_path.exists():
        return f"Repo not found: {to_path}"

    repo = Repo(to_path)

    try:
        repo.remotes.origin.fetch()

        if branch in repo.heads:
            repo.git.checkout(branch)
            repo.git.reset("--hard", f"origin/{branch}")
        elif f"origin/{branch}" in repo.refs:
            repo.git.checkout("-b", branch, f"origin/{branch}")
        else:
            repo.git.checkout(base_branch)
            repo.git.reset("--hard", f"origin/{base_branch}")
            repo.git.checkout("-b", branch)
    except Exception as error:
        return f"Failed to check out {branch} in {repo_name}: {error}"

    return f"Checked out {branch} in {repo_name}"
