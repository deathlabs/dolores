# Standard library imports.
from pathlib import Path
from os import getenv

# Third party imports.
from git import Repo
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
        None if successful, or an error message if failed.
    """

    # Define where to clone the repository.
    to_path = Path(DOWNLOADS_DIR) / repo_name

    # Check if the repository has already been cloned.
    if not to_path.exists():
        try:
            Repo.clone_from(url=url, to_path=to_path)
        except Exception as error:
            return f"Failed to clone the {repo_name} repository: {error}"
