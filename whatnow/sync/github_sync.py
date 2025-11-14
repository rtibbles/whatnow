"""GitHub Projects sync service using GraphQL API."""

import http.server
import json
import logging
import os
import pickle
import secrets
import socketserver
import threading
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests  # type: ignore[import-untyped]

from ..utils.retry import retry_on_network_error
from .github_credentials import (
    AUTHORIZATION_BASE_URL,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    REDIRECT_URI,
    SCOPES,
    TOKEN_URL,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def do_GET(self):
        """Handle GET request to callback URL."""
        # Parse the authorization code from the callback
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        if "code" in params:
            # Store the authorization code
            self.server.auth_code = params["code"][0]  # type: ignore
            self.server.auth_state = params.get("state", [None])[0]  # type: ignore

            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authentication successful!</h1>"
                b"<p>You can close this window and return to WhatNow.</p></body></html>"
            )
        else:
            # Error in authorization
            error = params.get("error", ["unknown"])[0]
            error_description = params.get("error_description", [""])[0]

            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<html><body><h1>Authentication failed</h1>"
                f"<p>Error: {error}</p>"
                f"<p>{error_description}</p></body></html>".encode()
            )

    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass


class GitHubSync:
    """Sync service for GitHub Projects."""

    GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

    def __init__(self, db, token: Optional[str], org: str, project_number: int):
        """Initialize GitHub sync service.

        Args:
            db: Database instance
            token: GitHub personal access token (optional if using OAuth)
            org: GitHub organization or user name
            project_number: Project number
        """
        self.db = db
        self.token = token
        self.org = org
        self.project_number = project_number
        self.oauth_token: Optional[str] = None

        # Token file path (stored next to database)
        data_dir = os.path.dirname(db.db_path)
        self.token_path = os.path.join(data_dir, "github_token.pickle")

        # Try OAuth authentication first
        if self._load_oauth_token():
            self.headers = {
                "Authorization": f"Bearer {self.oauth_token}",
                "Content-Type": "application/json",
            }
        elif token:
            # Fall back to PAT if OAuth not available
            self.headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        else:
            self.headers = {"Content-Type": "application/json"}

    def _load_oauth_token(self) -> bool:
        """Load OAuth token from disk.

        Returns:
            True if token loaded successfully, False otherwise
        """
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, "rb") as token_file:
                    token_data = pickle.load(token_file)
                    self.oauth_token = token_data.get("access_token")
                    logger.info("Loaded GitHub OAuth token from disk")
                    return True
            except Exception as e:
                logger.error(f"Failed to load OAuth token: {e}")
        return False

    def _save_oauth_token(self, token_data: Dict[str, Any]):
        """Save OAuth token to disk.

        Args:
            token_data: Token data from OAuth response
        """
        try:
            with open(self.token_path, "wb") as token_file:
                pickle.dump(token_data, token_file)
            logger.info("Saved GitHub OAuth token to disk")
        except Exception as e:
            logger.error(f"Failed to save OAuth token: {e}")

    def authenticate_oauth(self) -> bool:
        """Perform OAuth authentication flow.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Check if already authenticated
            if self._load_oauth_token():
                logger.info("Already authenticated with GitHub OAuth")
                return True

            logger.info("Starting OAuth flow for GitHub")

            # Generate random state for CSRF protection
            state = secrets.token_urlsafe(32)

            # Build authorization URL
            params = {
                "client_id": GITHUB_CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "scope": " ".join(SCOPES),
                "state": state,
            }
            auth_url = f"{AUTHORIZATION_BASE_URL}?{urllib.parse.urlencode(params)}"

            # Start local server to receive callback
            port = 8080
            server = socketserver.TCPServer(("localhost", port), OAuthCallbackHandler)
            server.auth_code = None  # type: ignore
            server.auth_state = None  # type: ignore

            # Run server in background thread
            server_thread = threading.Thread(target=server.handle_request, daemon=True)
            server_thread.start()

            # Open browser for authorization
            logger.info(f"Opening browser for GitHub authorization: {auth_url}")
            webbrowser.open(auth_url)

            # Wait for callback (timeout after 5 minutes)
            server_thread.join(timeout=300)

            # Check if we got the authorization code
            if not hasattr(server, "auth_code") or server.auth_code is None:  # type: ignore
                logger.error("Did not receive authorization code from GitHub")
                return False

            # Verify state matches
            if server.auth_state != state:  # type: ignore
                logger.error("State mismatch in OAuth callback - possible CSRF attack")
                return False

            auth_code: str = server.auth_code  # type: ignore

            # Exchange authorization code for access token
            token_params = {
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": auth_code,
                "redirect_uri": REDIRECT_URI,
            }

            response = requests.post(
                TOKEN_URL,
                data=token_params,
                headers={"Accept": "application/json"},
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return False

            token_data = response.json()

            if "error" in token_data:
                logger.error(
                    f"OAuth error: {token_data.get('error_description', token_data['error'])}"
                )
                return False

            if "access_token" not in token_data:
                logger.error("No access token in response")
                return False

            # Save token
            self.oauth_token = token_data["access_token"]
            self._save_oauth_token(token_data)

            # Update headers
            self.headers = {
                "Authorization": f"Bearer {self.oauth_token}",
                "Content-Type": "application/json",
            }

            logger.info("GitHub OAuth authentication successful")
            return True

        except Exception as e:
            logger.error(f"GitHub OAuth authentication failed: {e}")
            return False

    @retry_on_network_error(max_retries=4, initial_delay=2.0)
    def _execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query with automatic retry on network errors.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Response data dictionary

        Raises:
            Exception: If query fails after all retry attempts
        """
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.GRAPHQL_ENDPOINT, json=payload, headers=self.headers, timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")

        data: Dict[str, Any] = response.json()

        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        result: Dict[str, Any] = data.get("data", {})
        return result

    def _get_current_iteration(self) -> Optional[str]:
        """Get the current iteration title from the project.

        Returns:
            Current iteration title or None
        """
        query = """
        query($org: String!, $projectNumber: Int!) {
          organization(login: $org) {
            projectV2(number: $projectNumber) {
              field(name: "Iteration") {
                ... on ProjectV2IterationField {
                  configuration {
                    iterations {
                      id
                      title
                      startDate
                      duration
                    }
                    completedIterations {
                      id
                      title
                      startDate
                      duration
                    }
                  }
                }
              }
            }
          }
        }
        """

        user_query = query.replace("organization(login: $org)", "user(login: $org)")

        variables = {"org": self.org, "projectNumber": self.project_number}

        try:
            data = self._execute_query(query, variables)
            field_data = data.get("organization", {}).get("projectV2", {}).get("field")
        except Exception:
            try:
                data = self._execute_query(user_query, variables)
                field_data = data.get("user", {}).get("projectV2", {}).get("field")
            except Exception as e:
                logger.warning(f"Could not fetch iteration configuration: {e}")
                return None

        if not field_data:
            return None

        # Get current date
        now = datetime.now()

        # Check iterations to find current one
        iterations = field_data.get("configuration", {}).get("iterations", [])
        for iteration in iterations:
            if iteration.get("title", "").lower() == "@current":
                return str(iteration["title"])

            # Check if current date falls within iteration
            start_date_str = iteration.get("startDate")
            duration = iteration.get("duration")  # Duration in days

            if start_date_str and duration:
                try:
                    start_date = datetime.fromisoformat(start_date_str)
                    end_date = start_date + timedelta(days=duration)

                    if start_date <= now <= end_date:
                        return str(iteration["title"])
                except Exception:
                    pass

        return None

    def sync(self) -> bool:
        """Sync GitHub Projects data (only current iteration).

        Returns:
            True if sync was successful, False otherwise
        """
        try:
            logger.info(f"Starting GitHub sync for {self.org}/project/{self.project_number}")

            # Get current iteration
            current_iteration = self._get_current_iteration()
            if current_iteration:
                logger.info(f"Current iteration: {current_iteration}")
            else:
                logger.warning("Could not determine current iteration, syncing all items")

            # Query to get project items
            query = """
            query($org: String!, $projectNumber: Int!, $cursor: String) {
              organization(login: $org) {
                projectV2(number: $projectNumber) {
                  title
                  items(first: 100, after: $cursor) {
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                    nodes {
                      id
                      fieldValues(first: 20) {
                        nodes {
                          ... on ProjectV2ItemFieldTextValue {
                            text
                            field {
                              ... on ProjectV2FieldCommon {
                                name
                              }
                            }
                          }
                          ... on ProjectV2ItemFieldSingleSelectValue {
                            name
                            field {
                              ... on ProjectV2FieldCommon {
                                name
                              }
                            }
                          }
                          ... on ProjectV2ItemFieldIterationValue {
                            title
                            field {
                              ... on ProjectV2FieldCommon {
                                name
                              }
                            }
                          }
                        }
                      }
                      content {
                        ... on Issue {
                          id
                          title
                          body
                          state
                          url
                          labels(first: 10) {
                            nodes {
                              name
                            }
                          }
                          assignees(first: 10) {
                            nodes {
                              login
                            }
                          }
                          createdAt
                          updatedAt
                        }
                        ... on PullRequest {
                          id
                          title
                          body
                          state
                          url
                          labels(first: 10) {
                            nodes {
                              name
                            }
                          }
                          assignees(first: 10) {
                            nodes {
                              login
                            }
                          }
                          createdAt
                          updatedAt
                        }
                      }
                    }
                  }
                }
              }
            }
            """

            # Also support user projects
            user_query = query.replace("organization(login: $org)", "user(login: $org)")

            variables = {"org": self.org, "projectNumber": self.project_number, "cursor": None}

            all_items = []
            has_next_page = True

            # Fetch all pages
            while has_next_page:
                try:
                    data = self._execute_query(query, variables)
                    project_data = data.get("organization", {}).get("projectV2")
                except Exception:
                    # Try user query if organization query fails
                    data = self._execute_query(user_query, variables)
                    project_data = data.get("user", {}).get("projectV2")

                if not project_data:
                    raise Exception("Project not found")

                project_title = project_data.get("title")
                items = project_data.get("items", {})
                nodes = items.get("nodes", [])
                all_items.extend(nodes)

                page_info = items.get("pageInfo", {})
                has_next_page = page_info.get("hasNextPage", False)
                variables["cursor"] = page_info.get("endCursor")

            # Process and store items (filter by current iteration if available)
            synced_count = 0
            for item in all_items:
                content = item.get("content")
                if not content:
                    continue

                # Extract field values
                field_values = {}
                for field_value in item.get("fieldValues", {}).get("nodes", []):
                    field_name = field_value.get("field", {}).get("name")
                    if not field_name:
                        continue

                    if "text" in field_value:
                        field_values[field_name] = field_value["text"]
                    elif "name" in field_value:
                        field_values[field_name] = field_value["name"]
                    elif "title" in field_value:
                        field_values[field_name] = field_value["title"]

                # Get iteration
                iteration = field_values.get("Iteration") or field_values.get("Sprint")

                # Skip if not in current iteration (if we have a current iteration filter)
                if current_iteration and iteration != current_iteration:
                    continue

                # Extract labels
                labels = [label["name"] for label in content.get("labels", {}).get("nodes", [])]

                # Extract assignees
                assignees = [
                    assignee["login"] for assignee in content.get("assignees", {}).get("nodes", [])
                ]

                # Parse timestamps
                created_at = self._parse_timestamp(content.get("createdAt"))
                updated_at = self._parse_timestamp(content.get("updatedAt"))

                # Create task record
                task = {
                    "id": content["id"],
                    "title": content["title"],
                    "body": content.get("body"),
                    "state": content["state"],
                    "project_name": project_title,
                    "iteration": iteration,
                    "assignees": assignees,
                    "labels": labels,
                    "url": content["url"],
                    "created_at": created_at,
                    "updated_at": updated_at,
                }

                self.db.upsert_github_task(task)
                synced_count += 1

            logger.info(f"GitHub sync completed: {synced_count} items synced")

            # Update sync metadata
            self.db.update_sync_metadata("github", success=True)

            return True

        except Exception as e:
            logger.error(f"GitHub sync failed: {e}")
            self.db.update_sync_metadata("github", success=False, error_message=str(e))
            return False

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[int]:
        """Parse ISO 8601 timestamp to Unix timestamp.

        Args:
            timestamp_str: ISO 8601 timestamp string

        Returns:
            Unix timestamp or None
        """
        if not timestamp_str:
            return None

        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except Exception:
            return None
