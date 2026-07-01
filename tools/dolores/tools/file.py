# Standard library imports.
from pathlib import Path
from json import dumps

# Third party imports.
from fastmcp.tools import tool

# Local imports.
from dolores.config import DOWNLOADS_DIR


@tool(description="Lists all files in a cloned repository.")
async def list_files(repo_name: str) -> str:
    """List all files in a cloned repository.

    Returns:
        A JSON-formatted list of file paths relative to the repository root.
    """
    path = Path(f"{DOWNLOADS_DIR}/{repo_name}")
    if not path.exists():
        return f"Repo not found: {path}"
    paths = [
        str(p.relative_to(path))
        for p in path.rglob("*")
        if p.is_file() and ".git" not in p.parts
    ]
    return dumps(sorted(paths))


@tool(description="Reads the contents of a file in a cloned repository.")
async def read_file(repo_name: str, file_path: str) -> str:
    """Read the contents of a file in a cloned repository.

    Returns:
        The file contents as a string, or an error message if reading failed.
    """
    path = Path(f"{DOWNLOADS_DIR}/{repo_name}")
    target = (path / file_path).resolve()
    if not target.is_relative_to(path.resolve()):
        return "Access denied: path is outside the repository"
    if not target.exists():
        return f"File not found: {target}"
    try:
        return target.read_text()
    except Exception as e:
        return f"Error reading file: {e}"


@tool(description="Writes content to a file in a cloned repository.")
async def write_file(repo_name: str, file_path: str, content: str) -> str:
    """Writes content to a file in a cloned repository.

    Returns:
        A message indicating success or failure.
    """
    path = Path(f"{DOWNLOADS_DIR}/{repo_name}")

    target = (path / file_path).resolve()
    if not target.is_relative_to(path.resolve()):
        return "Access denied: path is outside the repository"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(content)
        return f"Wrote: {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"
