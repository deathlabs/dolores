# Standard library imports.
from os import environ

# Third party imports.
from github import Auth, Github
from github.GithubException import GithubException


class GitHubClient:
    def __init__(self, repo_name: str):
        token = Auth.Token(environ["GITHUB_PERSONAL_ACCESS_TOKEN"])
        self._client = Github(auth=token)
        self._repo = self._client.get_repo(repo_name)

    def ensure_branch(self, branch_name: str) -> None:
        try:
            self._repo.get_branch(branch_name)
        except GithubException as error:
            if error.status == 404:
                main_branch = self._repo.get_branch("main")
                self._repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}",
                    sha=main_branch.commit.sha,
                )
            else:
                raise

    def ensure_file(
        self, path: str, message: str, content: str, branch_name: str
    ) -> None:
        try:
            self._repo.get_contents(path, ref=branch_name)
        except GithubException as error:
            if error.status == 404:
                self._repo.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=branch_name,
                )
            else:
                raise

    def ensure_pull_request(self, branch_name: str, title: str, body: str) -> None:
        existing_pull_requests = self._repo.get_pulls(
            state="open",
            head=f"{self._repo.owner.login}:{branch_name}",
            base="main",
        )
        if existing_pull_requests.totalCount > 0:
            self.ensure_pull_request = existing_pull_requests[0]
        else:
            self._repo.create_pull(
                base="main",
                head=branch_name,
                title=title,
                body=body,
            )
