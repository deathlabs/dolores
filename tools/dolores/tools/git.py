# Standard library imports.
from pathlib import Path
from urllib.parse import urlparse

# Third party imports.
from git import Repo
from fastmcp.tools import tool

# Local imports.
from dolores.config import DOWNLOADS_DIR, GITHUB_PERSONAL_ACCESS_TOKEN


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
            repo = Repo.clone_from(url=url, to_path=to_path)
        except Exception as error:
            return f"Failed to clone the {repo_name} repository: {error}"

        # Bake the token into the origin URL so later push/pull calls
        # don't need an interactive credential prompt.
        token = GITHUB_PERSONAL_ACCESS_TOKEN
        if token:
            authed_url = f"https://x-access-token:{token}@github.com/{repo_name}.git"
            repo.remotes.origin.set_url(authed_url)

    return to_path.resolve()


@tool(description="Stage and commit changes in a cloned repository.")
async def git_commit(
    repo_name: str, commit_message: str, branch: str | None = None
) -> str:
    """Stage all changes and commit them in a cloned repository.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
        commit_message: The commit message to use for the changes.
        branch: The branch the repo is expected to be checked out on. If provided
            and the repo is on a different branch, the commit will fail.

    Returns:
        A message if successful, or an error message if failed.
    """
    repo_path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    if not repo_path.exists():
        return f"Repo not found: {repo_path}"

    repo = Repo(repo_path)

    if repo.head.is_detached:
        return f"Repo at {repo_path} is in a detached HEAD state"

    current_branch = repo.active_branch.name

    if branch is not None and branch != current_branch:
        return (
            f"Expected branch '{branch}' but repo is on '{current_branch}'. "
            f"Call git_checkout first."
        )

    if not repo.is_dirty(untracked_files=True):
        return f"No changes to commit on the {current_branch} branch"

    try:
        repo.git.add(A=True)
        repo.index.commit(commit_message)
    except Exception as error:
        return f"Failed to commit changes on {current_branch}: {error}"

    return f"Committed changes on {current_branch} in {repo_name}"


@tool(description="List local and remote branches in a cloned repository.")
async def git_list_branches(repo_name: str) -> str:
    """List branches in a cloned Git repository.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).

    Returns:
        A formatted list of local and remote branches, or an error message if failed.
    """
    repo_path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    if not repo_path.exists():
        return f"Repo not found: {repo_path}"

    repo = Repo(repo_path)

    try:
        repo.remotes.origin.fetch()
    except Exception as error:
        return f"Failed to fetch latest refs for {repo_name}: {error}"

    local_branches = [head.name for head in repo.heads]

    remote_branches = [
        ref.name.removeprefix("origin/")
        for ref in repo.remotes.origin.refs
        if ref.name != "origin/HEAD"
    ]

    if not local_branches and not remote_branches:
        return f"No branches found in {repo_name}"

    lines = [f"Branches in {repo_name}:"]

    if local_branches:
        lines.append("Local:")
        lines.extend(f"  - {name}" for name in sorted(local_branches))

    if remote_branches:
        lines.append("Remote:")
        lines.extend(f"  - {name}" for name in sorted(remote_branches))

    return "\n".join(lines)


@tool(
    description="Pull the latest changes for the current branch in a cloned repository."
)
async def git_pull(repo_name: str, branch: str | None = None) -> str:
    """Pull the latest changes for a cloned repository's current branch.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
        branch: The branch the repo is expected to be checked out on. If provided
            and the repo is on a different branch, the pull will fail.

    Returns:
        A message if successful, or an error message if failed.
    """
    repo_path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    if not repo_path.exists():
        return f"Repo not found: {repo_path}"

    repo = Repo(repo_path)

    if repo.head.is_detached:
        return f"Repo at {repo_path} is in a detached HEAD state"

    current_branch = repo.active_branch.name

    if branch is not None and branch != current_branch:
        return (
            f"Expected branch '{branch}' but repo is on '{current_branch}'. "
            f"Call git_checkout first."
        )

    try:
        repo.remotes.origin.pull(current_branch)
    except Exception as error:
        return f"Failed to pull {current_branch} in {repo_name}: {error}"

    return f"Pulled latest changes for {current_branch} in {repo_name}"


@tool(description="Push committed changes in a cloned repository.")
async def git_push(repo_name: str, branch: str | None = None) -> str:
    """Push committed changes in a cloned repository.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
        branch: The branch the repo is expected to be checked out on. If provided
            and the repo is on a different branch, the push will fail.

    Returns:
        A message if successful, or an error message if failed.
    """
    repo_path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    if not repo_path.exists():
        return f"Repo not found: {repo_path}"

    repo = Repo(repo_path)

    if repo.head.is_detached:
        return f"Repo at {repo_path} is in a detached HEAD state"

    current_branch = repo.active_branch.name

    if branch is not None and branch != current_branch:
        return (
            f"Expected branch '{branch}' but repo is on '{current_branch}'. "
            f"Call git_checkout first."
        )

    try:
        origin = repo.remotes.origin
        result = origin.push(current_branch)[0]
    except Exception as error:
        return f"Failed to push {current_branch} in {repo_name}: {error}"

    if result.flags & result.ERROR:
        return f"Push rejected for {current_branch} in {repo_name}: {result.summary}"

    return f"Pushed {current_branch} in {repo_name}"
