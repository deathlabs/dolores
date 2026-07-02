# Standard library imports.
from os import environ, getenv

# Get environment variables.
FASTMCP_PORT = environ["FASTMCP_PORT"]
DOWNLOADS_DIR = environ["DOWNLOADS_DIR"]
GITHUB_PERSONAL_ACCESS_TOKEN = getenv("GITHUB_PERSONAL_ACCESS_TOKEN", None)
