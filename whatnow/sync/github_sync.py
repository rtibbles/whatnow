"""GitHub Projects sync service using GraphQL API."""

import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubSync:
    """Sync service for GitHub Projects."""

    GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

    def __init__(self, db, token: str, org: str, project_number: int):
        """Initialize GitHub sync service.

        Args:
            db: Database instance
            token: GitHub personal access token
            org: GitHub organization or user name
            project_number: Project number
        """
        self.db = db
        self.token = token
        self.org = org
        self.project_number = project_number
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Response data dictionary

        Raises:
            Exception: If query fails
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.GRAPHQL_ENDPOINT,
            json=payload,
            headers=self.headers,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")

        data = response.json()

        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        return data.get("data", {})

    def sync(self) -> bool:
        """Sync GitHub Projects data.

        Returns:
            True if sync was successful, False otherwise
        """
        try:
            logger.info(f"Starting GitHub sync for {self.org}/project/{self.project_number}")

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

            variables = {
                "org": self.org,
                "projectNumber": self.project_number,
                "cursor": None
            }

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

            # Process and store items
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

                # Extract labels
                labels = [label["name"] for label in content.get("labels", {}).get("nodes", [])]

                # Extract assignees
                assignees = [assignee["login"] for assignee in content.get("assignees", {}).get("nodes", [])]

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
                    "iteration": field_values.get("Iteration") or field_values.get("Sprint"),
                    "assignees": assignees,
                    "labels": labels,
                    "url": content["url"],
                    "created_at": created_at,
                    "updated_at": updated_at
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
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return int(dt.timestamp())
        except Exception:
            return None
