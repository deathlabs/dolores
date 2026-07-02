# Standard library imports.
from pathlib import Path
from json import dumps

# Third party imports.
from fastmcp.tools import tool
from git import Repo, InvalidGitRepositoryError

# Local imports.
from dolores.config import DOWNLOADS_DIR


@tool(description="Lists all files in a cloned repository.")
async def list_files(repo_name: str) -> str:
    """List all files in a cloned repository.

    Args:
        repo_name: The name of the repository (e.g., "username/repo").

    Returns:
        A JSON-formatted list of file paths relative to the root of the repository.
    """

    # Define the path to the repository.
    path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    # Check if the repository exists.
    if not path.exists():
        return f"Repo not found: {path}"

    # List all files in the repository, excluding .git directories.
    paths = [
        str(p.relative_to(path))
        for p in path.rglob("*")
        if p.is_file() and ".git" not in p.parts
    ]

    # Return the list of file paths as a JSON-formatted string.
    return dumps(sorted(paths))


@tool(description="Reads the contents of a file in a cloned repository.")
async def read_file(repo_name: str, file_path: str) -> str:
    """Read the contents of a file in a cloned repository.

    Args:
        repo_name: The name of the repository (e.g., "username/repo").
        file_path: The path to the file relative to the root of the repository.

    Returns:
        The file contents as a string, or an error message if reading failed.
    """
    # Define the path to the repository.
    path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    # Check if the repository exists.
    target = (path / file_path).resolve()

    # Check if the target file is within the repository directory to prevent directory traversal attacks.
    if not target.is_relative_to(path.resolve()):
        return "Access denied: path is outside the repository"

    # Check if the target file exists.
    if not target.exists():
        return f"File not found: {target}"

    # Read and return the contents of the file.
    try:
        return target.read_text()
    except Exception as error:
        return f"Error reading file: {error}"


@tool(
    description="Writes content to a file in a cloned repository. Requires the branch the repository must currently be checked out on; fails if the branches don't match."
)
async def write_file(repo_name: str, file_path: str, content: str, branch: str) -> str:
    """Writes content to a file in a cloned repository.

    Args:
        repo_name: The name of the repository (e.g., "username/repo").
        file_path: The path to the file relative to the root of the repository.
        content: The content to write to the file.
        branch: The branch the repository must currently be checked out on.
            Call checkout_branch first if this doesn't match the current branch.

    Returns:
        A message indicating success or failure.
    """

    # Define the path to the repository.
    path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    # Check if the repository exists.
    if not path.exists():
        return f"Repo not found: {path}"

    # Verify the repo is on the expected branch before writing anything.
    try:
        repo = Repo(path)
        current_branch = repo.active_branch.name
    except InvalidGitRepositoryError:
        return f"{path} is not a git repository"
    except TypeError:
        # active_branch raises TypeError in detached HEAD state.
        return f"Repo at {path} is in a detached HEAD state, expected branch '{branch}'"

    if current_branch != branch:
        return (
            f"Expected branch '{branch}' but repo is on '{current_branch}'. "
            f"Call checkout_branch first."
        )

    # Check if the target file is within the repository directory to prevent directory traversal attacks.
    target = (path / file_path).resolve()
    if not target.is_relative_to(path.resolve()):
        return "Access denied: path is outside the repository"

    target.parent.mkdir(parents=True, exist_ok=True)

    # Write the content to the file.
    try:
        target.write_text(content)
        return f"Wrote: {file_path} on branch {branch}"
    except Exception as error:
        return f"Error writing file: {error}"
