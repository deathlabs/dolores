# Standard library imports.
from pathlib import Path
from json import dumps
from subprocess import run

# Third party imports.
from fastmcp.tools import tool
from github import Auth, Github
from github.GithubException import GithubException

# Local imports.
from dolores.config import DOWNLOADS_DIR, GITHUB_PERSONAL_ACCESS_TOKEN


def get_github_client() -> Github:
    """Creates a GitHub client using the GITHUB_PERSONAL_ACCESS_TOKEN environment variable.

    Returns:
        A GitHub client.
    """

    if not GITHUB_PERSONAL_ACCESS_TOKEN:
        raise ValueError(
            "The GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set."
        )

    return Github(auth=Auth.Token(GITHUB_PERSONAL_ACCESS_TOKEN))


@tool(description="Creates a branch in a GitHub repository.")
async def create_github_branch(
    repo_name: str, base_branch: str, new_branch: str
) -> str:
    """Create a new branch in a GitHub repository.

    Args:
        repo_name: The name of the repository (e.g., "username/repo").
        base_branch: The name of the branch to base the new branch on (e.g., "main").
        new_branch: The name of the new branch to create (e.g., "feature-branch").

    Returns:
        A message if successful, or an error message if failed.
    """

    # Init a GitHub client.
    client = get_github_client()

    # Get the repository object.
    try:
        repo = client.get_repo(repo_name)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find the {repo_name} repository"
        return f"Failed to access the {repo_name} repository: {error}"

    # Get the base branch object.
    try:
        source = repo.get_branch(base_branch)
    except GithubException as error:
        if error.status == 404:
            return (
                f"Failed to find the {base_branch} branch in the {repo_name} repository"
            )
        return f"Failed to access the {base_branch} branch in the {repo_name} repository: {error}"

    # Create the new branch.
    try:
        repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=source.commit.sha)
    except GithubException as error:
        if error.status == 422:
            return (
                f"The {new_branch} branch already exists in the {repo_name} repository"
            )
        return f"Failed to create the {new_branch} branch in the {repo_name} repository: {error}"

    return f"Successfully created the {new_branch} branch in the {repo_name} repository"


@tool(description="Fetches all pull requests for a given GitHub repository.")
async def get_github_pull_requests(repo_name: str) -> str:
    """Fetch all pull requests for a given GitHub repository.

    Args:
        repo_name: The name of the repository (e.g., "username/repo").

    Returns:
        A list of pull requests if successful, or an error message if failed.
    """

    # Init a GitHub client.
    client = get_github_client()

    # Get the repository object.
    try:
        repo = client.get_repo(repo_name)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find the {repo_name} repository"
        return f"Failed to access the {repo_name} repository: {error}"

    # Get the pull requests for the repository.
    pull_requests = dumps(
        [
            {
                "number": pull_request.number,
                "title": pull_request.title,
                "url": pull_request.html_url,
                "branch": pull_request.head.ref,
                "created_at": pull_request.created_at.isoformat(),
            }
            for pull_request in repo.get_pulls(state="all")
        ]
    )
    return pull_requests


@tool(description="Fetches the status of a pull request in a GitHub repository.")
async def get_github_pull_request_status(
    repo_name: str, pull_request_number: int
) -> str:
    """Get the status of a pull request in a GitHub repository.

    Args:
        repo_name: The name of the repository (e.g., "username/repo").
        pull_request_number: The number of the pull request to check.

    Returns:
        A message if successful, or an error message if failed.
    """

    # Init a GitHub client.
    client = get_github_client()

    # Get the repository object.
    try:
        repo = client.get_repo(repo_name)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find the {repo_name} repository"
        return f"Failed to access the {repo_name} repository: {error}"

    # Get the pull request object.
    try:
        pull_request = repo.get_pull(pull_request_number)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find pull request #{pull_request_number} in the {repo_name} repository"
        return f"Failed to access pull request #{pull_request_number} in the {repo_name} repository: {error}"

    # Return the status of the pull request.
    return f"Pull request #{pull_request_number} in the {repo_name} repository is currently '{pull_request.state}' with '{pull_request.mergeable_state}' mergeable state."


@tool(description="Commits and pushes changes in a cloned repository.")
async def update_github_branch(
    repo_name: str, commit_message: str, branch: str | None = None
) -> str:
    """Commit and push changes in a cloned repository.

    Args:
        repo_name: The name of the repository (e.g., "username/repo").
        commit_message: The commit message to use for the changes.
        branch: The branch the repository is expected to be checked out on.
            If provided, the commit fails if the repo is on a different branch.
            If omitted, commits to whatever branch is currently checked out.

    Returns:
        A message if successful, or an error message if failed.
    """

    # Init a GitHub client.
    client = get_github_client()

    # Define where to find the repository locally.
    repo_path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    # Check if the repository has been cloned.
    if not repo_path.exists():
        return f"Repo not found: {repo_path}"

    # Get the repository object.
    try:
        repo = client.get_repo(repo_name)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find the {repo_name} repository"
        return f"Failed to access the {repo_name} repository: {error}"

    # Get the current branch name.
    current_branch = run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        cwd=repo_path,
    ).stdout.strip()

    # Check for detached HEAD, which has no branch name.
    if not current_branch:
        return f"Repo at {repo_path} is in a detached HEAD state"

    # If a branch was specified, enforce it matches what's checked out.
    if branch is not None and branch != current_branch:
        return (
            f"Expected branch '{branch}' but repo is on '{current_branch}'. "
            f"Call checkout_branch first."
        )

    target_branch = branch or current_branch

    # Stage all changes (new, modified, deleted) so nothing is missed.
    run(["git", "add", "-A"], cwd=repo_path)

    # Get the list of changed files relative to the last commit.
    changed = (
        run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )
        .stdout.strip()
        .splitlines()
    )

    # Check if there's anything to push.
    if not changed:
        return f"No changes to push on the {target_branch} branch"

    # Commit and push each changed file via the GitHub API.
    for file_path in changed:
        target = repo_path / file_path

        # Skip deleted files; not yet supported.
        if not target.exists():
            continue

        content = target.read_text()

        # Update the file if it already exists in the repository, otherwise create it.
        try:
            existing = repo.get_contents(file_path, ref=target_branch)
            repo.update_file(file_path, commit_message, content, existing.sha, branch=target_branch)
        except Exception:
            repo.create_file(file_path, commit_message, content, branch=target_branch)

    return f"Pushed {len(changed)} file(s) to {target_branch}"


@tool(description="Creates a pull request in a GitHub repository.")
async def create_github_pull_request(
    repo_name: str, base_branch: str, head_branch: str, title: str, body: str
) -> str:
    """Create a pull request in a GitHub repository.
    Args:
        repo_name: The name of the repository (e.g., "username/repo").
        base_branch: The name of the branch you want the changes pulled into.
        head_branch: The name of the branch where your changes are implemented.
        title: The title of the pull request.
        body: The description or body of the pull request.

    Returns:
        A message if successful, or an error message if failed.
    """

    # Init a GitHub client.
    client = get_github_client()

    # Get the repository object.
    try:
        repo = client.get_repo(repo_name)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find the {repo_name} repository"
        return f"Failed to access the {repo_name} repository: {error}"

    # Create the pull request.
    try:
        repo.create_pull(base=base_branch, head=head_branch, title=title, body=body)
    except GithubException as error:
        return f"Failed to create a pull request in the {repo_name} repository: {error}"

    return f"Successfully created a pull request in the {repo_name} repository"
