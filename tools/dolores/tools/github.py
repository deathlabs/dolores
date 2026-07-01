# Third party imports.
from fastmcp.tools import tool
from github import Auth, Github
from github.GithubException import GithubException

# Local imports.
from dolores.config import GITHUB_PERSONAL_ACCESS_TOKEN


@tool(description="Creates a branch in a GitHub repository.")
async def create_github_branch(
    repo_name: str, base_branch: str, new_branch: str
) -> None | str:
    """Create a new branch in a GitHub repository.

    Args:
        repo_name: The name of the repository (e.g., "username/repo").
        base_branch: The name of the branch to base the new branch on (e.g., "main").
        new_branch: The name of the new branch to create (e.g., "feature-branch").

    Returns:
        None if successful, or an error message if failed.
    """

    # Get the GitHub personal access token from environment variables.
    if not GITHUB_PERSONAL_ACCESS_TOKEN:
        return "The GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set."

    # Create a GitHub client.
    client = Github(auth=Auth.Token(GITHUB_PERSONAL_ACCESS_TOKEN))

    # Get the repository object.
    try:
        repo = client.get_repo(repo_name)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find the {repo_name} repository"

    # Get the base branch object.
    try:
        source = repo.get_branch(base_branch)
    except GithubException as error:
        if error.status == 404:
            return (
                f"Failed to find the {base_branch} branch in the {repo_name} repository"
            )

    # Create the new branch.
    try:
        repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=source.commit.sha)
    except GithubException as error:
        if error.status == 422:
            return (
                f"The {new_branch} branch already exists in the {repo_name} repository"
            )
        else:
            return f"Failed to create the {new_branch} branch in the {repo_name} repository: {error}"


@tool(description="Creates a pull request in a GitHub repository.")
async def create_github_pull_request(
    repo_name: str, base_branch: str, head_branch: str, title: str, body: str
) -> None | str:
    """Create a pull request in a GitHub repository.
    Args:
        repo_name: The name of the repository (e.g., "username/repo").
        base_branch: The name of the branch you want the changes pulled into.
        head_branch: The name of the branch where your changes are implemented.
        title: The title of the pull request.
        body: The description or body of the pull request.

    Returns:
        None if successful, or an error message if failed.
    """

    # Get the GitHub personal access token from environment variables.
    if not GITHUB_PERSONAL_ACCESS_TOKEN:
        return "The GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set."

    # Create a GitHub client.
    client = Github(auth=Auth.Token(GITHUB_PERSONAL_ACCESS_TOKEN))

    # Get the repository object.
    try:
        repo = client.get_repo(repo_name)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find the {repo_name} repository"

    # Create the pull request.
    try:
        repo.create_pull(base=base_branch, head=head_branch, title=title, body=body)
    except GithubException as error:
        return f"Failed to create a pull request in the {repo_name} repository: {error}"
