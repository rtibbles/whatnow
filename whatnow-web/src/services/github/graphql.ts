import { GitHubOAuth } from './oauth';
import { retryWithBackoff, shouldRetryGitHub } from '../../utils/retry';

export interface GitHubIssue {
  id: string;
  title: string;
  body: string;
  state: 'OPEN' | 'CLOSED';
  url: string;
  labels: Array<{ name: string }>;
  assignees: Array<{ login: string }>;
  createdAt: string;
  updatedAt: string;
}

export interface GitHubProjectItem {
  id: string;
  content?: GitHubIssue;
  fieldValues: {
    nodes: Array<{
      field?: { name: string };
      name?: string; // For single select fields (Status, Priority)
      text?: string; // For text fields
      number?: number; // For number fields
    }>;
  };
}

/**
 * GitHub GraphQL API client
 */
export class GitHubGraphQL {
  private readonly endpoint = 'https://api.github.com/graphql';
  private oauth: GitHubOAuth;

  constructor(oauth: GitHubOAuth) {
    this.oauth = oauth;
  }

  /**
   * Execute GraphQL query with retry logic
   */
  private async query<T = any>(query: string, variables: Record<string, any> = {}): Promise<T> {
    return retryWithBackoff(
      async () => {
        const token = await this.oauth.getAccessToken();

        const response = await fetch(this.endpoint, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
            Accept: 'application/json'
          },
          body: JSON.stringify({ query, variables })
        });

        if (!response.ok) {
          // Attach response for retry logic to check status
          const error: any = new Error(`GitHub API error: ${response.statusText}`);
          error.status = response.status;
          error.headers = response.headers;
          throw error;
        }

        const data = await response.json();

        if (data.errors) {
          throw new Error(`GraphQL errors: ${JSON.stringify(data.errors)}`);
        }

        return data.data;
      },
      {
        maxRetries: 4,
        initialDelay: 2000,
        shouldRetry: shouldRetryGitHub,
        onRetry: (error, attempt, delay) => {
          console.log(
            `[GitHub GraphQL] Retry attempt ${attempt} after ${Math.round(delay)}ms:`,
            error instanceof Error ? error.message : error
          );
        }
      }
    );
  }

  /**
   * Get user's assigned issues
   */
  async getAssignedIssues(limit: number = 50): Promise<GitHubIssue[]> {
    const query = `
      query($limit: Int!) {
        viewer {
          issues(first: $limit, states: OPEN, orderBy: {field: UPDATED_AT, direction: DESC}) {
            nodes {
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
              assignees(first: 5) {
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
    `;

    const data = await this.query<{ viewer: { issues: { nodes: any[] } } }>(query, { limit });
    return data.viewer.issues.nodes.map(issue => ({
      ...issue,
      labels: issue.labels.nodes,
      assignees: issue.assignees.nodes
    }));
  }

  /**
   * Get organization's project items
   */
  async getProjectItems(org: string, projectNumber: number, limit: number = 50): Promise<GitHubProjectItem[]> {
    const query = `
      query($org: String!, $projectNumber: Int!, $limit: Int!) {
        organization(login: $org) {
          projectV2(number: $projectNumber) {
            items(first: $limit) {
              nodes {
                id
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
                    assignees(first: 5) {
                      nodes {
                        login
                      }
                    }
                    createdAt
                    updatedAt
                  }
                }
                fieldValues(first: 20) {
                  nodes {
                    ... on ProjectV2ItemFieldSingleSelectValue {
                      field {
                        ... on ProjectV2FieldCommon {
                          name
                        }
                      }
                      name
                    }
                    ... on ProjectV2ItemFieldTextValue {
                      field {
                        ... on ProjectV2FieldCommon {
                          name
                        }
                      }
                      text
                    }
                    ... on ProjectV2ItemFieldNumberValue {
                      field {
                        ... on ProjectV2FieldCommon {
                          name
                        }
                      }
                      number
                    }
                  }
                }
              }
            }
          }
        }
      }
    `;

    const data = await this.query<{
      organization: { projectV2: { items: { nodes: GitHubProjectItem[] } } }
    }>(query, { org, projectNumber, limit });

    return data.organization.projectV2.items.nodes;
  }

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<{ login: string; name: string }> {
    const query = `
      query {
        viewer {
          login
          name
        }
      }
    `;

    const data = await this.query<{ viewer: { login: string; name: string } }>(query);
    return data.viewer;
  }
}
