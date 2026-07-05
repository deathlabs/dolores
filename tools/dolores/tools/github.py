# Standard library imports.
from pathlib import Path
from json import dumps
from subprocess import run

# Third party imports.
from fastmcp.tools import tool
from github import Auth, Github
from github.GithubException import GithubException

# Local imports.
from dolores.config import GITHUB_PERSONAL_ACCESS_TOKEN


@tool(description="Create a branch in a GitHub repository.")
async def create_branch(repo_name: str, base_branch: str, new_branch: str) -> str:
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


@tool(description="Create a pull request in a GitHub repository.")
async def create_pull_request(
    repo_name: str, base_branch: str, head_branch: str, title: str, body: str
) -> str:
    """Create a pull request in a GitHub repository.
    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
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


def get_github_client() -> Github:
    """Create a GitHub client using the GITHUB_PERSONAL_ACCESS_TOKEN environment variable.

    Returns:
        A GitHub client.
    """

    if not GITHUB_PERSONAL_ACCESS_TOKEN:
        raise ValueError(
            "The GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set."
        )

    return Github(auth=Auth.Token(GITHUB_PERSONAL_ACCESS_TOKEN))


@tool(description="Get all pull request issue comments for a GitHub pull request.")
async def get_pull_request_issue_comments(
    repo_name: str,
    pull_request_number: int,
) -> str:
    """Get all issue comments for a GitHub pull request.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
        pull_request_number: The pull request number.

    Returns:
        A list of pull request issue comments if successful, or an error message
        if failed.
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
            return f"Failed to find pull request #{pull_request_number}"
        return f"Failed to access pull request #{pull_request_number}: {error}"

    # Get the issue comments for the pull request.
    comments = dumps(
        [
            {
                "id": comment.id,
                "user": comment.user.login,
                "body": comment.body,
                "created_at": comment.created_at.isoformat(),
                "updated_at": comment.updated_at.isoformat(),
            }
            for comment in pull_request.get_issue_comments()
        ]
    )

    return comments


@tool(description="Get all pull request review comments for a GitHub pull request.")
async def get_pull_request_review_comments(
    repo_name: str,
    pull_request_number: int,
) -> str:
    """Get all pull request review comments for a GitHub pull request.

    These are comments left directly on lines of a diff, as opposed to general
    conversation comments on the pull request.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
        pull_request_number: The pull request number.

    Returns:
        A list of pull request review comments if successful, or an error message
        if failed.
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
            return f"Failed to find pull request #{pull_request_number}"
        return f"Failed to access pull request #{pull_request_number}: {error}"

    # Get the inline review comments for the pull request.
    comments = dumps(
        [
            {
                "id": comment.id,
                "user": comment.user.login,
                "body": comment.body,
                "path": comment.path,
                "line": comment.line,
                "created_at": comment.created_at.isoformat(),
                "updated_at": comment.updated_at.isoformat(),
            }
            for comment in pull_request.get_review_comments()
        ]
    )

    return comments


@tool(description="Get the status of a pull request in a GitHub repository.")
async def get_pull_request_status(repo_name: str, pull_request_number: int) -> str:
    """Get the status of a pull request in a GitHub repository.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
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


@tool(description="Get all pull requests for a given GitHub repository.")
async def get_pull_requests(repo_name: str) -> str:
    """Get all pull requests for a given GitHub repository.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).

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


@tool(
    description="Reply to an existing issue comment (general PR conversation) on a pull request."
)
async def reply_to_pull_request_issue_comment(
    repo_name: str, pull_request_number: int, comment_id: int, body: str
) -> str:
    """Reply to an existing issue comment on a pull request.

    Issue comments are general conversation comments on the pull request,
    not comments left inline on a specific line of a diff.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
        pull_request_number: The number of the pull request the comment belongs to.
        comment_id: The ID of the issue comment to reply to.
        body: The text of the reply (e.g., an acknowledgment or a clarifying question).

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
        issue = repo.get_issue(pull_request_number)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find pull request #{pull_request_number} in the {repo_name} repository"
        return f"Failed to access pull request #{pull_request_number} in the {repo_name} repository: {error}"

    # Get the issue comment object.
    try:
        issue_comment = issue.get_comment(comment_id)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find comment #{comment_id} on pull request #{pull_request_number} in the {repo_name} repository"
        return f"Failed to access comment #{comment_id} on pull request #{pull_request_number} in the {repo_name} repository: {error}"

    # Reply to the issue comment.
    try:
        issue_comment.reply(f"@{issue_comment.user.login} {body}")
    except GithubException as error:
        return f"Failed to reply to comment #{comment_id} on pull request #{pull_request_number} in the {repo_name} repository: {error}"

    return f"Successfully replied to comment #{comment_id} on pull request #{pull_request_number} in the {repo_name} repository"


@tool(
    description="Reply to an existing inline review comment (diff comment) on a pull request."
)
async def reply_to_pull_request_review_comment(
    repo_name: str, pull_request_number: int, comment_id: int, body: str
) -> str:
    """Reply to an existing inline review comment on a pull request.

    Review comments are left directly on a line of a diff, as opposed to
    general conversation comments on the pull request.

    Args:
        repo_name: The full name of the repository (i.e., owner/repo).
        pull_request_number: The number of the pull request the comment belongs to.
        comment_id: The ID of the review comment to reply to.
        body: The text of the reply (e.g., an acknowledgment or a clarifying question).

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

    # Reply to the review comment.
    try:
        pull_request.create_review_comment_reply(comment_id, body)
    except GithubException as error:
        if error.status == 404:
            return f"Failed to find comment #{comment_id} on pull request #{pull_request_number} in the {repo_name} repository"
        return f"Failed to reply to comment #{comment_id} on pull request #{pull_request_number} in the {repo_name} repository: {error}"

    return f"Successfully replied to comment #{comment_id} on pull request #{pull_request_number} in the {repo_name} repository"
