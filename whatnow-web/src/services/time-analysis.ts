/**
 * Time analysis service
 * Analyzes ping data to calculate time spent on activities, tags, and TODOs
 */

import type { PingDocument } from '../db/schemas/ping.schema';
import { getDatabase } from '../db/database';

export interface TimeEntry {
  pingId: string;
  timestamp: number;
  tags: string[];
  todoId: string | null;
  todoType: 'github' | 'local' | 'meeting' | null;
  notes: string | null;
  isMeeting: boolean;
  weight: number; // Time weight in minutes (based on average gap)
}

export interface TagStatistics {
  tag: string;
  totalMinutes: number;
  percentage: number;
  pingCount: number;
}

export interface TodoStatistics {
  todoId: string;
  todoType: 'github' | 'local' | 'meeting';
  totalMinutes: number;
  percentage: number;
  pingCount: number;
  tags: string[];
}

export interface TimeAnalysisResult {
  totalPings: number;
  totalMinutes: number;
  averageGapMinutes: number;
  periodStart: number;
  periodEnd: number;
  byTag: TagStatistics[];
  byTodo: TodoStatistics[];
  meetingMinutes: number;
  meetingPercentage: number;
}

export interface DateRange {
  start: Date;
  end: Date;
}

/**
 * Time analysis service
 */
export class TimeAnalysisService {
  /**
   * Calculate time statistics for a date range
   */
  async analyzeTimeRange(range: DateRange, averageGapMinutes: number = 45): Promise<TimeAnalysisResult> {
    const db = await getDatabase();

    // Fetch pings in range
    const pings = await db.pings
      .find({
        selector: {
          timestamp: {
            $gte: range.start.getTime(),
            $lte: range.end.getTime()
          }
        },
        sort: [{ timestamp: 'asc' }]
      })
      .exec();

    if (pings.length === 0) {
      return this.emptyResult(range, averageGapMinutes);
    }

    // Convert to plain objects for analysis
    const pingDocs = pings.map(p => p.toJSON() as PingDocument);

    // Build time entries
    const entries = this.buildTimeEntries(pingDocs, averageGapMinutes);

    // Calculate statistics
    const totalMinutes = entries.reduce((sum, e) => sum + e.weight, 0);
    const meetingMinutes = entries
      .filter(e => e.isMeeting)
      .reduce((sum, e) => sum + e.weight, 0);

    return {
      totalPings: pingDocs.length,
      totalMinutes,
      averageGapMinutes,
      periodStart: range.start.getTime(),
      periodEnd: range.end.getTime(),
      byTag: this.calculateTagStatistics(entries, totalMinutes),
      byTodo: this.calculateTodoStatistics(entries, totalMinutes),
      meetingMinutes,
      meetingPercentage: totalMinutes > 0 ? (meetingMinutes / totalMinutes) * 100 : 0
    };
  }

  /**
   * Build time entries from ping documents
   */
  private buildTimeEntries(pings: PingDocument[], averageGapMinutes: number): TimeEntry[] {
    return pings.map(ping => ({
      pingId: ping.id,
      timestamp: ping.timestamp,
      tags: ping.tags || [],
      todoId: ping.todoId,
      todoType: ping.todoType,
      notes: ping.notes,
      isMeeting: ping.isMeeting || false,
      weight: averageGapMinutes
    }));
  }

  /**
   * Calculate statistics by tag
   */
  private calculateTagStatistics(entries: TimeEntry[], totalMinutes: number): TagStatistics[] {
    const tagMap = new Map<string, {
      minutes: number;
      count: number;
    }>();

    // Aggregate by tag
    for (const entry of entries) {
      for (const tag of entry.tags) {
        if (!tagMap.has(tag)) {
          tagMap.set(tag, {
            minutes: 0,
            count: 0
          });
        }

        const tagData = tagMap.get(tag)!;
        tagData.minutes += entry.weight;
        tagData.count++;
      }
    }

    // Convert to array and sort by time
    return Array.from(tagMap.entries())
      .map(([tag, data]) => ({
        tag,
        totalMinutes: data.minutes,
        percentage: totalMinutes > 0 ? (data.minutes / totalMinutes) * 100 : 0,
        pingCount: data.count
      }))
      .sort((a, b) => b.totalMinutes - a.totalMinutes);
  }

  /**
   * Calculate statistics by TODO
   */
  private calculateTodoStatistics(entries: TimeEntry[], totalMinutes: number): TodoStatistics[] {
    const todoMap = new Map<string, {
      todoType: 'github' | 'local' | 'meeting';
      minutes: number;
      count: number;
      tags: Set<string>;
    }>();

    // Aggregate by TODO
    for (const entry of entries) {
      if (!entry.todoId || !entry.todoType) continue;

      if (!todoMap.has(entry.todoId)) {
        todoMap.set(entry.todoId, {
          todoType: entry.todoType,
          minutes: 0,
          count: 0,
          tags: new Set()
        });
      }

      const todoData = todoMap.get(entry.todoId)!;
      todoData.minutes += entry.weight;
      todoData.count++;
      entry.tags.forEach(tag => todoData.tags.add(tag));
    }

    // Convert to array and sort by time
    return Array.from(todoMap.entries())
      .map(([todoId, data]) => ({
        todoId,
        todoType: data.todoType,
        totalMinutes: data.minutes,
        percentage: totalMinutes > 0 ? (data.minutes / totalMinutes) * 100 : 0,
        pingCount: data.count,
        tags: Array.from(data.tags)
      }))
      .sort((a, b) => b.totalMinutes - a.totalMinutes);
  }

  /**
   * Get all pings for export
   */
  async getAllPings(range?: DateRange): Promise<PingDocument[]> {
    const db = await getDatabase();

    if (range) {
      const pings = await db.pings
        .find({
          selector: {
            timestamp: {
              $gte: range.start.getTime(),
              $lte: range.end.getTime()
            }
          }
        })
        .sort({ timestamp: 'asc' })
        .exec();
      return pings.map(p => p.toJSON() as PingDocument);
    } else {
      const pings = await db.pings
        .find()
        .sort({ timestamp: 'asc' })
        .exec();
      return pings.map(p => p.toJSON() as PingDocument);
    }
  }

  /**
   * Get common date ranges
   */
  static getCommonRanges(): Record<string, DateRange> {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const thisWeekStart = new Date(today);
    thisWeekStart.setDate(today.getDate() - today.getDay()); // Sunday
    const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0);

    return {
      today: {
        start: today,
        end: new Date(today.getTime() + 24 * 60 * 60 * 1000 - 1)
      },
      yesterday: {
        start: new Date(today.getTime() - 24 * 60 * 60 * 1000),
        end: new Date(today.getTime() - 1)
      },
      thisWeek: {
        start: thisWeekStart,
        end: new Date(thisWeekStart.getTime() + 7 * 24 * 60 * 60 * 1000 - 1)
      },
      lastWeek: {
        start: new Date(thisWeekStart.getTime() - 7 * 24 * 60 * 60 * 1000),
        end: new Date(thisWeekStart.getTime() - 1)
      },
      thisMonth: {
        start: thisMonthStart,
        end: new Date(thisMonthStart.getTime() + 31 * 24 * 60 * 60 * 1000)
      },
      lastMonth: {
        start: lastMonthStart,
        end: lastMonthEnd
      },
      last7Days: {
        start: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
        end: now
      },
      last30Days: {
        start: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000),
        end: now
      }
    };
  }

  /**
   * Create empty result
   */
  private emptyResult(range: DateRange, averageGapMinutes: number): TimeAnalysisResult {
    return {
      totalPings: 0,
      totalMinutes: 0,
      averageGapMinutes,
      periodStart: range.start.getTime(),
      periodEnd: range.end.getTime(),
      byTag: [],
      byTodo: [],
      meetingMinutes: 0,
      meetingPercentage: 0
    };
  }

  /**
   * Format minutes as hours and minutes
   */
  static formatDuration(minutes: number): string {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);

    if (hours === 0) {
      return `${mins}m`;
    } else if (mins === 0) {
      return `${hours}h`;
    } else {
      return `${hours}h ${mins}m`;
    }
  }

  /**
   * Format percentage
   */
  static formatPercentage(percentage: number): string {
    return `${percentage.toFixed(1)}%`;
  }
}
