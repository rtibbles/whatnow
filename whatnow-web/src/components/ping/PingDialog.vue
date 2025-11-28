<script setup lang="ts">
import { ref, computed } from 'vue';
import { useTodos } from '../../composables/useTodos';
import { getDatabase } from '../../db/database';
import type { PingDocument } from '../../db/schemas/ping.schema';
import type { CalendarEventDocument } from '../../db/schemas/calendar-event.schema';
import type { UnifiedTodo } from '../../composables/useTodos';

const props = defineProps<{
  pingIndex: number;
  pingTime: number;
  show: boolean;
}>();

const emit = defineEmits<{
  complete: [pingIndex: number];
  dismiss: [];
}>();

const { activeTodos, allTags } = useTodos();

// Form state
const selectedTodoId = ref<string | null>(null);
const selectedTodoType = ref<'local' | 'github' | 'meeting' | null>(null);
const customTags = ref<string[]>([]);
const notes = ref('');
const newTagInput = ref('');
const isMeeting = ref(false);
const saving = ref(false);

// Find selected TODO
const selectedTodo = computed<UnifiedTodo | null>(() => {
  if (!selectedTodoId.value || !selectedTodoType.value) return null;
  const todo = activeTodos.value.find(
    t => t.id === selectedTodoId.value && t.type === selectedTodoType.value
  );
  return todo || null;
});

// Combined tags (from selected TODO + custom tags)
const combinedTags = computed<string[]>(() => {
  const tags = [...customTags.value];
  if (selectedTodo.value?.tags) {
    tags.push(...selectedTodo.value.tags);
  }
  return Array.from(new Set(tags)); // Remove duplicates
});

// Select a TODO
const selectTodo = (todo: UnifiedTodo) => {
  selectedTodoId.value = todo.id;
  selectedTodoType.value = todo.type;
  isMeeting.value = todo.type === 'meeting';
};

// Add custom tag
const addTag = () => {
  const tag = newTagInput.value.trim();
  if (tag && !customTags.value.includes(tag)) {
    customTags.value.push(tag);
    newTagInput.value = '';
  }
};

// Remove tag
const removeTag = (tag: string) => {
  customTags.value = customTags.value.filter(t => t !== tag);
};

// Add tag from suggestions
const addSuggestedTag = (tag: string) => {
  if (!customTags.value.includes(tag)) {
    customTags.value.push(tag);
  }
};

// Handle quick tag input via keyboard
const handleTagKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    addTag();
  }
};

// Save ping response
const savePing = async () => {
  if (saving.value) return;

  saving.value = true;
  try {
    const db = await getDatabase();

    // Get eventId if this is a meeting
    let eventId: string | null = null;
    if (isMeeting.value && selectedTodo.value?.type === 'meeting') {
      const calendarEvent = selectedTodo.value.rawData as CalendarEventDocument;
      eventId = calendarEvent.eventId;
    }

    const ping: PingDocument = {
      id: crypto.randomUUID(),
      timestamp: props.pingTime,
      todoId: selectedTodoId.value,
      todoType: selectedTodoType.value,
      tags: combinedTags.value,
      notes: notes.value.trim() || null,
      eventId,
      isMeeting: isMeeting.value,
      createdAt: Date.now()
    };

    await db.pings.insert(ping);
    emit('complete', props.pingIndex);
    resetForm();
  } catch (error) {
    console.error('Failed to save ping:', error);
    alert('Failed to save ping. Please try again.');
  } finally {
    saving.value = false;
  }
};

// Skip/dismiss ping
const skipPing = () => {
  emit('dismiss');
  resetForm();
};

// Reset form
const resetForm = () => {
  selectedTodoId.value = null;
  selectedTodoType.value = null;
  customTags.value = [];
  notes.value = '';
  newTagInput.value = '';
  isMeeting.value = false;
};

// Format time for display
const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleTimeString();
};

// Get priority badge color
const getPriorityColor = (priority: number): string => {
  if (priority >= 12) return 'bg-red-100 text-red-800 border-red-300';
  if (priority >= 8) return 'bg-orange-100 text-orange-800 border-orange-300';
  if (priority >= 4) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
  return 'bg-green-100 text-green-800 border-green-300';
};
</script>

<template>
  <div v-if="show" class="ping-dialog-overlay" @click.self="skipPing">
    <div class="ping-dialog">
      <div class="dialog-header">
        <h2 class="text-2xl font-bold">WhatNow Ping!</h2>
        <p class="text-sm text-gray-600">{{ formatTime(pingTime) }}</p>
      </div>

      <div class="dialog-body">
        <!-- Question -->
        <div class="mb-6">
          <h3 class="text-lg font-medium mb-2">What are you working on?</h3>
        </div>

        <!-- TODO Selection -->
        <div class="mb-6">
          <label class="block text-sm font-medium mb-2">Select a TODO:</label>
          <div class="todo-list">
            <button
              v-for="todo in activeTodos"
              :key="`${todo.type}-${todo.id}`"
              @click="selectTodo(todo)"
              :class="[
                'todo-item',
                selectedTodoId === todo.id && selectedTodoType === todo.type ? 'selected' : ''
              ]"
            >
              <div class="todo-content">
                <div class="todo-title">{{ todo.title }}</div>
                <div class="todo-meta">
                  <span :class="['priority-badge', getPriorityColor(todo.priority)]">
                    Priority: {{ todo.priority }}
                  </span>
                  <span class="type-badge">{{ todo.type }}</span>
                </div>
              </div>
            </button>
            <div v-if="activeTodos.length === 0" class="text-sm text-gray-500 p-4">
              No active TODOs. Add tags or notes below.
            </div>
          </div>
        </div>

        <!-- Meeting checkbox -->
        <div class="mb-6">
          <label class="flex items-center">
            <input
              type="checkbox"
              v-model="isMeeting"
              class="mr-2"
            />
            <span class="text-sm font-medium">This is a meeting</span>
          </label>
        </div>

        <!-- Tags -->
        <div class="mb-6">
          <label class="block text-sm font-medium mb-2">Tags:</label>

          <!-- Current tags -->
          <div class="tag-list mb-2">
            <span
              v-for="tag in customTags"
              :key="tag"
              class="tag"
            >
              {{ tag }}
              <button @click="removeTag(tag)" class="tag-remove">×</button>
            </span>
            <span v-if="customTags.length === 0" class="text-xs text-gray-400">
              No tags yet
            </span>
          </div>

          <!-- Tag input -->
          <div class="flex gap-2 mb-2">
            <input
              v-model="newTagInput"
              @keydown="handleTagKeydown"
              type="text"
              placeholder="Add a tag..."
              class="tag-input"
            />
            <button @click="addTag" class="btn-secondary">Add</button>
          </div>

          <!-- Suggested tags -->
          <div v-if="allTags.length > 0" class="text-xs">
            <span class="text-gray-600">Suggestions:</span>
            <button
              v-for="tag in allTags.slice(0, 10)"
              :key="tag"
              @click="addSuggestedTag(tag)"
              class="suggested-tag"
              :disabled="customTags.includes(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </div>

        <!-- Notes -->
        <div class="mb-6">
          <label class="block text-sm font-medium mb-2">Notes (optional):</label>
          <textarea
            v-model="notes"
            placeholder="Any additional context..."
            rows="3"
            class="notes-input"
          />
        </div>
      </div>

      <div class="dialog-footer">
        <button @click="skipPing" class="btn-secondary" :disabled="saving">
          Skip
        </button>
        <button @click="savePing" class="btn-primary" :disabled="saving">
          {{ saving ? 'Saving...' : 'Log Activity' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ping-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.ping-dialog {
  background: white;
  border-radius: 0.5rem;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.dialog-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.dialog-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.todo-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
}

.todo-item {
  width: 100%;
  text-align: left;
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.15s;
}

.todo-item:last-child {
  border-bottom: none;
}

.todo-item:hover {
  background-color: #f9fafb;
}

.todo-item.selected {
  background-color: #dbeafe;
  border-left: 3px solid #3b82f6;
}

.todo-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.todo-title {
  font-weight: 500;
  color: #111827;
}

.todo-meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.priority-badge {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  border: 1px solid;
  font-weight: 500;
}

.type-badge {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  background-color: #f3f4f6;
  color: #6b7280;
  text-transform: uppercase;
  font-weight: 600;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  min-height: 2rem;
  align-items: center;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  background-color: #3b82f6;
  color: white;
  border-radius: 9999px;
  font-size: 0.875rem;
  gap: 0.5rem;
}

.tag-remove {
  font-size: 1.25rem;
  line-height: 1;
  font-weight: bold;
  color: white;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.tag-remove:hover {
  color: #dbeafe;
}

.tag-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.tag-input:focus {
  outline: none;
  border-color: #3b82f6;
  ring: 2px;
  ring-color: #3b82f6;
  ring-opacity: 0.5;
}

.suggested-tag {
  margin-left: 0.5rem;
  margin-top: 0.25rem;
  padding: 0.125rem 0.5rem;
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
  cursor: pointer;
}

.suggested-tag:hover:not(:disabled) {
  background-color: #e5e7eb;
}

.suggested-tag:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notes-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  resize: vertical;
}

.notes-input:focus {
  outline: none;
  border-color: #3b82f6;
  ring: 2px;
  ring-color: #3b82f6;
  ring-opacity: 0.5;
}

.btn-primary {
  padding: 0.5rem 1.5rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.5rem 1.5rem;
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #f9fafb;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
