import { getDatabase } from '../../db/database';
import { GitHubGraphQL, type GitHubIssue } from './graphql';
import { GitHubOAuth } from './oauth';
import type { GitHubTaskDocument } from '../../db/schemas/github-task.schema';

/**
 * GitHub sync service
 * Syncs assigned issues from GitHub to local database
 */
export class GitHubSync {
  private oauth: GitHubOAuth;
  private graphql: GitHubGraphQL;

  constructor() {
    this.oauth = new GitHubOAuth();
    this.graphql = new GitHubGraphQL(this.oauth);
  }

  /**
   * Perform full sync of GitHub issues
   */
  async performSync(): Promise<{ added: number; updated: number; errors: number }> {
    const stats = { added: 0, updated: 0, errors: 0 };

    try {
      // Check if authenticated
      const isAuth = await this.oauth.isAuthenticated();
      if (!isAuth) {
        console.log('Not authenticated with GitHub');
        return stats;
      }

      // Fetch assigned issues
      const issues = await this.graphql.getAssignedIssues(100);
      const db = await getDatabase();

      // Sync each issue
      for (const issue of issues) {
        try {
          const task = this.convertToGitHubTask(issue);

          // Check if task already exists
          const existing = await db.github_tasks
            .findOne({ selector: { id: task.id } })
            .exec();

          if (existing) {
            // Update existing task
            await existing.update({
              $set: {
                title: task.title,
                body: task.body,
                state: task.state,
                urgency: task.urgency,
                importance: task.importance,
                labels: task.labels,
                url: task.url,
                updatedAt: task.updatedAt,
                syncedAt: task.syncedAt
              }
            });
            stats.updated++;
          } else {
            // Insert new task
            await db.github_tasks.insert(task);
            stats.added++;
          }
        } catch (error) {
          console.error('Error syncing issue:', issue.id, error);
          stats.errors++;
        }
      }

      console.log(`GitHub sync complete:`, stats);
      return stats;

    } catch (error) {
      console.error('GitHub sync failed:', error);
      throw error;
    }
  }

  /**
   * Convert GitHub issue to GitHubTaskDocument
   */
  private convertToGitHubTask(issue: GitHubIssue): GitHubTaskDocument {
    // Extract assignee logins
    const assignees = issue.assignees.map(a => a.login);

    // Extract label names
    const labels = issue.labels.map(l => l.name);

    // Determine state
    let state: 'OPEN' | 'IN_PROGRESS' | 'DONE';
    if (issue.state === 'CLOSED') {
      state = 'DONE';
    } else {
      // Check labels for in-progress indicators
      const inProgressLabels = ['in progress', 'wip', 'working'];
      const hasInProgress = labels.some(l =>
        inProgressLabels.includes(l.toLowerCase())
      );
      state = hasInProgress ? 'IN_PROGRESS' : 'OPEN';
    }

    // Calculate urgency and importance from labels
    const urgency = this.calculateUrgency(labels);
    const importance = this.calculateImportance(labels);

    return {
      id: issue.id,
      title: issue.title,
      body: issue.body || '',
      state,
      projectName: 'GitHub Issues', // Default project name
      iteration: 'Current', // Default iteration
      urgency,
      importance,
      assignees,
      labels,
      url: issue.url,
      createdAt: new Date(issue.createdAt).getTime(),
      updatedAt: new Date(issue.updatedAt).getTime(),
      syncedAt: Date.now()
    };
  }

  /**
   * Calculate urgency from labels (1-4, higher is more urgent)
   */
  private calculateUrgency(labels: string[]): 1 | 2 | 3 | 4 {
    const labelLower = labels.map(l => l.toLowerCase());

    if (labelLower.some(l => l.includes('critical') || l.includes('urgent') || l.includes('p0'))) {
      return 4;
    }
    if (labelLower.some(l => l.includes('high') || l.includes('p1'))) {
      return 3;
    }
    if (labelLower.some(l => l.includes('low') || l.includes('p3'))) {
      return 1;
    }
    return 2; // Default medium
  }

  /**
   * Calculate importance from labels (1-4, higher is more important)
   */
  private calculateImportance(labels: string[]): 1 | 2 | 3 | 4 {
    const labelLower = labels.map(l => l.toLowerCase());

    if (labelLower.some(l => l.includes('bug') || l.includes('security'))) {
      return 4;
    }
    if (labelLower.some(l => l.includes('feature') || l.includes('enhancement'))) {
      return 3;
    }
    if (labelLower.some(l => l.includes('documentation') || l.includes('chore'))) {
      return 1;
    }
    return 2; // Default medium
  }

  /**
   * Get OAuth instance (for external use)
   */
  getOAuth(): GitHubOAuth {
    return this.oauth;
  }
}

/**
 * Standalone function for use in service worker
 */
export async function performGitHubSync(): Promise<void> {
  const sync = new GitHubSync();
  await sync.performSync();
}
