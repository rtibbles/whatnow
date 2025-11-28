import { ref, computed, onMounted } from 'vue';
import { getDatabase } from '../db/database';
import type { LocalTodoDocument } from '../db/schemas/local-todo.schema';
import type { GitHubTaskDocument } from '../db/schemas/github-task.schema';
import type { CalendarEventDocument } from '../db/schemas/calendar-event.schema';

export interface UnifiedTodo {
  id: string;
  title: string;
  type: 'local' | 'github' | 'meeting';
  urgency?: number;
  importance?: number;
  priority: number; // Calculated priority score
  tags?: string[];
  rawData: LocalTodoDocument | GitHubTaskDocument | CalendarEventDocument;
}

/**
 * Composable for unified access to all TODO types
 * Combines local TODOs, GitHub tasks, and upcoming calendar events
 */
export function useTodos() {
  const localTodos = ref<LocalTodoDocument[]>([]);
  const githubTasks = ref<GitHubTaskDocument[]>([]);
  const upcomingMeetings = ref<CalendarEventDocument[]>([]);
  const loading = ref(true);

  /**
   * Calculate priority score (higher is more urgent/important)
   */
  const calculatePriority = (urgency: number, importance: number): number => {
    return urgency * importance;
  };

  /**
   * Unified list of all TODOs sorted by priority
   */
  const allTodos = computed<UnifiedTodo[]>(() => {
    const unified: UnifiedTodo[] = [];

    // Add local TODOs
    localTodos.value.forEach(todo => {
      unified.push({
        id: todo.id,
        title: todo.text,
        type: 'local',
        urgency: todo.urgency,
        importance: todo.importance,
        priority: calculatePriority(todo.urgency, todo.importance),
        tags: todo.tags,
        rawData: todo
      });
    });

    // Add GitHub tasks
    githubTasks.value.forEach(task => {
      unified.push({
        id: task.id,
        title: task.title,
        type: 'github',
        urgency: task.urgency,
        importance: task.importance,
        priority: calculatePriority(task.urgency, task.importance),
        tags: task.labels,
        rawData: task
      });
    });

    // Add upcoming meetings (next 2 hours)
    const twoHoursFromNow = Date.now() + (2 * 60 * 60 * 1000);
    upcomingMeetings.value.forEach(event => {
      if (event.startTime <= twoHoursFromNow) {
        // For meetings, priority based on how soon they start
        const minutesUntil = (event.startTime - Date.now()) / 1000 / 60;
        const urgencyScore = minutesUntil < 30 ? 4 : minutesUntil < 60 ? 3 : 2;

        unified.push({
          id: event.id,
          title: event.summary,
          type: 'meeting',
          urgency: urgencyScore,
          importance: 3, // Meetings are generally important
          priority: urgencyScore * 3,
          rawData: event
        });
      }
    });

    // Sort by priority (descending)
    return unified.sort((a, b) => b.priority - a.priority);
  });

  /**
   * Active TODOs (high priority, most relevant)
   */
  const activeTodos = computed<UnifiedTodo[]>(() => {
    return allTodos.value.filter(todo => {
      // For local TODOs, check isActive flag
      if (todo.type === 'local') {
        return (todo.rawData as LocalTodoDocument).isActive;
      }

      // For GitHub tasks, check state
      if (todo.type === 'github') {
        const task = todo.rawData as GitHubTaskDocument;
        return task.state === 'OPEN' || task.state === 'IN_PROGRESS';
      }

      // All upcoming meetings are considered active
      return true;
    });
  });

  /**
   * Load all TODOs from database
   */
  const loadTodos = async () => {
    loading.value = true;
    try {
      const db = await getDatabase();

      // Load active local TODOs
      const localDocs = await db.local_todos
        .find({
          selector: {
            isActive: true
          },
          sort: [
            { urgency: 'desc' },
            { importance: 'desc' }
          ]
        })
        .exec();
      localTodos.value = localDocs.map(doc => doc.toJSON()) as LocalTodoDocument[];

      // Load active GitHub tasks
      const githubDocs = await db.github_tasks
        .find({
          selector: {
            state: {
              $in: ['OPEN', 'IN_PROGRESS']
            }
          },
          sort: [
            { urgency: 'desc' },
            { importance: 'desc' }
          ]
        })
        .exec();
      githubTasks.value = githubDocs.map(doc => doc.toJSON()) as GitHubTaskDocument[];

      // Load upcoming calendar events (next 24 hours)
      const now = Date.now();
      const tomorrow = now + (24 * 60 * 60 * 1000);
      const eventDocs = await db.calendar_events
        .find({
          selector: {
            startTime: {
              $gte: now,
              $lte: tomorrow
            }
          },
          sort: [
            { startTime: 'asc' }
          ]
        })
        .exec();
      upcomingMeetings.value = eventDocs.map(doc => doc.toJSON()) as CalendarEventDocument[];

    } catch (error) {
      console.error('Failed to load TODOs:', error);
    } finally {
      loading.value = false;
    }
  };

  /**
   * Find TODO by ID and type
   */
  const findTodo = (id: string, type: 'local' | 'github' | 'meeting'): UnifiedTodo | undefined => {
    return allTodos.value.find(todo => todo.id === id && todo.type === type);
  };

  /**
   * Add a new local TODO
   */
  const addLocalTodo = async (text: string, urgency: 1 | 2 | 3 | 4, importance: 1 | 2 | 3 | 4, tags: string[] = []): Promise<LocalTodoDocument> => {
    const db = await getDatabase();

    const todo: LocalTodoDocument = {
      id: crypto.randomUUID(),
      text,
      tags,
      isActive: true,
      urgency,
      importance,
      createdAt: Date.now(),
      completedAt: null
    };

    await db.local_todos.insert(todo);
    await loadTodos(); // Refresh list

    return todo;
  };

  /**
   * Complete a local TODO
   */
  const completeLocalTodo = async (id: string): Promise<void> => {
    const db = await getDatabase();

    const doc = await db.local_todos.findOne({ selector: { id } }).exec();
    if (doc) {
      await doc.update({
        $set: {
          isActive: false,
          completedAt: Date.now()
        }
      });
      await loadTodos(); // Refresh list
    }
  };

  /**
   * Get all unique tags from all TODOs
   */
  const allTags = computed<string[]>(() => {
    const tagSet = new Set<string>();

    localTodos.value.forEach(todo => {
      todo.tags.forEach(tag => tagSet.add(tag));
    });

    githubTasks.value.forEach(task => {
      task.labels.forEach(label => tagSet.add(label));
    });

    return Array.from(tagSet).sort();
  });

  onMounted(() => {
    loadTodos();
  });

  return {
    allTodos,
    activeTodos,
    localTodos,
    githubTasks,
    upcomingMeetings,
    loading,
    allTags,
    loadTodos,
    findTodo,
    addLocalTodo,
    completeLocalTodo
  };
}
