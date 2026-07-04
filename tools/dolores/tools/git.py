# Standard library imports.
from pathlib import Path
from urllib.parse import urlparse

# Third party imports.
from git import Repo
from fastmcp.tools import tool

# Local imports.
from dolores.config import DOWNLOADS_DIR


@tool(
    description="Check out a branch in a cloned repository, creating it locally if needed."
)
async def git_checkout(repo_name: str, branch: str, base_branch: str) -> str:
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


@tool(description="Clone a Git repository.")
async def git_clone(url: str) -> None | str:
    """Clone a Git repository.

    Args:
        url: The URL of the Git repository to clone.

    Returns:
        The path to the cloned repository if successful, or an error message if failed.
    """

    # Extract the repository name from the URL.
    repo_name = urlparse(url).path.strip("/").removesuffix(".git")

    # Define where to clone the repository.
    to_path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    # Check if the repository has already been cloned.
    if not to_path.exists():
        try:
            Repo.clone_from(url=url, to_path=to_path)
        except Exception as error:
            return f"Failed to clone the {repo_name} repository: {error}"

    return to_path.resolve()


@tool(description="")
async def git_commit():
    return


@tool()
async def git_pull():
    return


@tool(description="Push changes in a cloned repository.")
async def git_push(
    repo_name: str, commit_message: str, branch: str | None = None
) -> str:
    """Push changes in a cloned repository.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
        commit_message: The commit message to use for the changes.
        branch: The branch the repository is expected to be checked out on. If provided and the repo is on a different branch, the commit will fail. If omitted, the commit will be made to whatever branch is currently checked out.

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
            repo.update_file(
                file_path, commit_message, content, existing.sha, branch=target_branch
            )
        except Exception:
            repo.create_file(file_path, commit_message, content, branch=target_branch)

    return f"Pushed {len(changed)} file(s) to {target_branch}"
