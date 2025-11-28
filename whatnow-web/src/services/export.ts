/**
 * Export service
 * Exports ping data and analysis results in various formats
 */

import type { PingDocument } from '../db/schemas/ping.schema';
import type { TimeAnalysisResult } from './time-analysis';
import dayjs from 'dayjs';

export type ExportFormat = 'csv' | 'json' | 'tsv';

/**
 * Export service
 */
export class ExportService {
  /**
   * Export pings to CSV
   */
  static exportPingsToCSV(pings: PingDocument[]): string {
    const headers = [
      'Timestamp',
      'Date',
      'Time',
      'Tags',
      'Notes',
      'TODO ID',
      'TODO Type',
      'Is Meeting',
      'Event ID'
    ];

    const rows = pings.map(ping => [
      ping.timestamp.toString(),
      dayjs(ping.timestamp).format('YYYY-MM-DD'),
      dayjs(ping.timestamp).format('HH:mm:ss'),
      this.escapeCSV((ping.tags || []).join(', ')),
      this.escapeCSV(ping.notes || ''),
      this.escapeCSV(ping.todoId || ''),
      this.escapeCSV(ping.todoType || ''),
      ping.isMeeting ? 'Yes' : 'No',
      ping.eventId || ''
    ]);

    return [headers, ...rows]
      .map(row => row.join(','))
      .join('\n');
  }

  /**
   * Export pings to TSV (Tab-separated values)
   */
  static exportPingsToTSV(pings: PingDocument[]): string {
    const headers = [
      'Timestamp',
      'Date',
      'Time',
      'Tags',
      'Notes',
      'TODO ID',
      'TODO Type',
      'Is Meeting',
      'Event ID'
    ];

    const rows = pings.map(ping => [
      ping.timestamp.toString(),
      dayjs(ping.timestamp).format('YYYY-MM-DD'),
      dayjs(ping.timestamp).format('HH:mm:ss'),
      (ping.tags || []).join(', '),
      ping.notes || '',
      ping.todoId || '',
      ping.todoType || '',
      ping.isMeeting ? 'Yes' : 'No',
      ping.eventId || ''
    ]);

    return [headers, ...rows]
      .map(row => row.join('\t'))
      .join('\n');
  }

  /**
   * Export pings to JSON
   */
  static exportPingsToJSON(pings: PingDocument[]): string {
    const data = pings.map(ping => ({
      id: ping.id,
      timestamp: ping.timestamp,
      date: dayjs(ping.timestamp).format('YYYY-MM-DD'),
      time: dayjs(ping.timestamp).format('HH:mm:ss'),
      tags: ping.tags || [],
      notes: ping.notes,
      todoId: ping.todoId,
      todoType: ping.todoType,
      isMeeting: ping.isMeeting || false,
      eventId: ping.eventId,
      createdAt: ping.createdAt
    }));

    return JSON.stringify(data, null, 2);
  }

  /**
   * Export time analysis to CSV
   */
  static exportAnalysisToCSV(analysis: TimeAnalysisResult): string {
    const sections: string[] = [];

    // Summary section
    sections.push('Summary');
    sections.push('Metric,Value');
    sections.push(`Total Pings,${analysis.totalPings}`);
    sections.push(`Total Time,${this.formatMinutes(analysis.totalMinutes)}`);
    sections.push(`Average Gap,${analysis.averageGapMinutes} minutes`);
    sections.push(`Meeting Time,${this.formatMinutes(analysis.meetingMinutes)}`);
    sections.push(`Meeting Percentage,${analysis.meetingPercentage.toFixed(1)}%`);
    sections.push(`Period Start,${dayjs(analysis.periodStart).format('YYYY-MM-DD HH:mm:ss')}`);
    sections.push(`Period End,${dayjs(analysis.periodEnd).format('YYYY-MM-DD HH:mm:ss')}`);
    sections.push('');

    // By Tag
    sections.push('Time by Tag');
    sections.push('Tag,Minutes,Hours,Percentage,Ping Count');
    for (const tag of analysis.byTag) {
      sections.push(
        [
          this.escapeCSV(tag.tag),
          tag.totalMinutes.toFixed(1),
          (tag.totalMinutes / 60).toFixed(2),
          tag.percentage.toFixed(1) + '%',
          tag.pingCount.toString()
        ].join(',')
      );
    }
    sections.push('');

    // By TODO
    if (analysis.byTodo.length > 0) {
      sections.push('Time by TODO');
      sections.push('TODO ID,TODO Type,Minutes,Hours,Percentage,Ping Count,Tags');
      for (const todo of analysis.byTodo) {
        sections.push(
          [
            this.escapeCSV(todo.todoId),
            this.escapeCSV(todo.todoType),
            todo.totalMinutes.toFixed(1),
            (todo.totalMinutes / 60).toFixed(2),
            todo.percentage.toFixed(1) + '%',
            todo.pingCount.toString(),
            this.escapeCSV(todo.tags.join(', '))
          ].join(',')
        );
      }
      sections.push('');
    }

    return sections.join('\n');
  }

  /**
   * Export time analysis to JSON
   */
  static exportAnalysisToJSON(analysis: TimeAnalysisResult): string {
    const data = {
      summary: {
        totalPings: analysis.totalPings,
        totalMinutes: analysis.totalMinutes,
        totalHours: analysis.totalMinutes / 60,
        averageGapMinutes: analysis.averageGapMinutes,
        meetingMinutes: analysis.meetingMinutes,
        meetingPercentage: analysis.meetingPercentage,
        periodStart: dayjs(analysis.periodStart).format('YYYY-MM-DD HH:mm:ss'),
        periodEnd: dayjs(analysis.periodEnd).format('YYYY-MM-DD HH:mm:ss')
      },
      byTag: analysis.byTag.map(tag => ({
        tag: tag.tag,
        minutes: tag.totalMinutes,
        hours: tag.totalMinutes / 60,
        percentage: tag.percentage,
        pingCount: tag.pingCount
      })),
      byTodo: analysis.byTodo.map(todo => ({
        todoId: todo.todoId,
        todoType: todo.todoType,
        minutes: todo.totalMinutes,
        hours: todo.totalMinutes / 60,
        percentage: todo.percentage,
        pingCount: todo.pingCount,
        tags: todo.tags
      }))
    };

    return JSON.stringify(data, null, 2);
  }

  /**
   * Download data as a file
   */
  static downloadFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  /**
   * Export pings with automatic download
   */
  static async exportPings(
    pings: PingDocument[],
    format: ExportFormat,
    filename?: string
  ): Promise<void> {
    const timestamp = dayjs().format('YYYY-MM-DD-HHmmss');
    const defaultFilename = `whatnow-pings-${timestamp}`;

    let content: string;
    let mimeType: string;
    let extension: string;

    switch (format) {
      case 'csv':
        content = this.exportPingsToCSV(pings);
        mimeType = 'text/csv';
        extension = 'csv';
        break;
      case 'tsv':
        content = this.exportPingsToTSV(pings);
        mimeType = 'text/tab-separated-values';
        extension = 'tsv';
        break;
      case 'json':
        content = this.exportPingsToJSON(pings);
        mimeType = 'application/json';
        extension = 'json';
        break;
    }

    const finalFilename = filename || `${defaultFilename}.${extension}`;
    this.downloadFile(content, finalFilename, mimeType);
  }

  /**
   * Export analysis with automatic download
   */
  static async exportAnalysis(
    analysis: TimeAnalysisResult,
    format: 'csv' | 'json',
    filename?: string
  ): Promise<void> {
    const timestamp = dayjs().format('YYYY-MM-DD-HHmmss');
    const defaultFilename = `whatnow-analysis-${timestamp}`;

    let content: string;
    let mimeType: string;
    let extension: string;

    switch (format) {
      case 'csv':
        content = this.exportAnalysisToCSV(analysis);
        mimeType = 'text/csv';
        extension = 'csv';
        break;
      case 'json':
        content = this.exportAnalysisToJSON(analysis);
        mimeType = 'application/json';
        extension = 'json';
        break;
    }

    const finalFilename = filename || `${defaultFilename}.${extension}`;
    this.downloadFile(content, finalFilename, mimeType);
  }

  /**
   * Escape CSV field
   */
  private static escapeCSV(field: string): string {
    if (field.includes(',') || field.includes('"') || field.includes('\n')) {
      return `"${field.replace(/"/g, '""')}"`;
    }
    return field;
  }

  /**
   * Format minutes as "Xh Ym"
   */
  private static formatMinutes(minutes: number): string {
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
}
