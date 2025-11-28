<script setup lang="ts">
import { ref, computed } from 'vue';
import { useTodos } from '../../composables/useTodos';
import { getDatabase } from '../../db/database';
import type { PingDocument } from '../../db/schemas/ping.schema';

interface MissedPing {
  index: number;
  time: number;
}

const props = defineProps<{
  missedPings: MissedPing[];
  show: boolean;
}>();

const emit = defineEmits<{
  complete: [pingIndices: number[]];
  dismiss: [];
}>();

const { activeTodos } = useTodos();

// Batch mode: apply same activity to all pings
const useBatchMode = ref(true);
const batchTodoId = ref<string | null>(null);
const batchTodoType = ref<'local' | 'github' | 'meeting' | null>(null);
const batchTags = ref<string[]>([]);
const batchNotes = ref('');
const saving = ref(false);

// Individual mode: separate activity for each ping
interface PingResponse {
  pingIndex: number;
  pingTime: number;
  todoId: string | null;
  todoType: 'local' | 'github' | 'meeting' | null;
  tags: string[];
  notes: string;
  isMeeting: boolean;
}

const individualResponses = ref<Map<number, PingResponse>>(new Map());

// Initialize individual responses for each missed ping
const initializeResponses = () => {
  props.missedPings.forEach(ping => {
    if (!individualResponses.value.has(ping.index)) {
      individualResponses.value.set(ping.index, {
        pingIndex: ping.index,
        pingTime: ping.time,
        todoId: null,
        todoType: null,
        tags: [],
        notes: '',
        isMeeting: false
      });
    }
  });
};

// Initialize on mount
initializeResponses();

// Format time for display
const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleTimeString();
};

// Format date for display
const formatDate = (timestamp: number): string => {
  return new Date(timestamp).toLocaleDateString();
};

// Save all missed pings
const saveAll = async () => {
  if (saving.value) return;

  saving.value = true;
  try {
    const db = await getDatabase();
    const pingIndices: number[] = [];

    if (useBatchMode.value) {
      // Batch mode: same activity for all pings
      for (const missedPing of props.missedPings) {
        const ping: PingDocument = {
          id: crypto.randomUUID(),
          timestamp: missedPing.time,
          todoId: batchTodoId.value,
          todoType: batchTodoType.value,
          tags: batchTags.value,
          notes: batchNotes.value.trim() || null,
          eventId: null,
          isMeeting: false,
          createdAt: Date.now()
        };

        await db.pings.insert(ping);
        pingIndices.push(missedPing.index);
      }
    } else {
      // Individual mode: different activity for each ping
      for (const [pingIndex, response] of individualResponses.value) {
        const ping: PingDocument = {
          id: crypto.randomUUID(),
          timestamp: response.pingTime,
          todoId: response.todoId,
          todoType: response.todoType,
          tags: response.tags,
          notes: response.notes.trim() || null,
          eventId: null,
          isMeeting: response.isMeeting,
          createdAt: Date.now()
        };

        await db.pings.insert(ping);
        pingIndices.push(pingIndex);
      }
    }

    emit('complete', pingIndices);
  } catch (error) {
    console.error('Failed to save missed pings:', error);
    alert('Failed to save missed pings. Please try again.');
  } finally {
    saving.value = false;
  }
};

// Skip all missed pings (mark as missed)
const skipAll = () => {
  emit('dismiss');
};

// Select batch TODO
const selectBatchTodo = (todo: typeof activeTodos.value[0]) => {
  batchTodoId.value = todo.id;
  batchTodoType.value = todo.type;
};

// Add batch tag
const newBatchTag = ref('');
const addBatchTag = () => {
  const tag = newBatchTag.value.trim();
  if (tag && !batchTags.value.includes(tag)) {
    batchTags.value.push(tag);
    newBatchTag.value = '';
  }
};

// Remove batch tag
const removeBatchTag = (tag: string) => {
  batchTags.value = batchTags.value.filter(t => t !== tag);
};

// Handle batch tag keyboard
const handleBatchTagKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    addBatchTag();
  }
};

// Count of pings
const pingCount = computed(() => props.missedPings.length);
</script>

<template>
  <div v-if="show" class="missed-pings-overlay" @click.self="skipAll">
    <div class="missed-pings-dialog">
      <div class="dialog-header">
        <h2 class="text-2xl font-bold">Missed Pings</h2>
        <p class="text-sm text-gray-600">
          You missed {{ pingCount }} ping{{ pingCount !== 1 ? 's' : '' }} while away
        </p>
      </div>

      <div class="dialog-body">
        <!-- Mode toggle -->
        <div class="mb-6 p-4 bg-gray-50 rounded-lg">
          <label class="flex items-center cursor-pointer">
            <input
              type="checkbox"
              v-model="useBatchMode"
              class="mr-3"
            />
            <div>
              <div class="font-medium">Batch Mode</div>
              <div class="text-xs text-gray-600">
                Apply the same activity to all {{ pingCount }} pings
              </div>
            </div>
          </label>
        </div>

        <!-- Batch mode UI -->
        <div v-if="useBatchMode" class="batch-mode">
          <h3 class="text-lg font-medium mb-4">What were you working on?</h3>

          <!-- TODO Selection -->
          <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Select a TODO:</label>
            <div class="todo-list">
              <button
                v-for="todo in activeTodos"
                :key="`${todo.type}-${todo.id}`"
                @click="selectBatchTodo(todo)"
                :class="[
                  'todo-item',
                  batchTodoId === todo.id && batchTodoType === todo.type ? 'selected' : ''
                ]"
              >
                <div class="todo-title">{{ todo.title }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ todo.type }}</div>
              </button>
            </div>
          </div>

          <!-- Tags -->
          <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Tags:</label>
            <div class="tag-list mb-2">
              <span v-for="tag in batchTags" :key="tag" class="tag">
                {{ tag }}
                <button @click="removeBatchTag(tag)" class="tag-remove">×</button>
              </span>
            </div>
            <div class="flex gap-2">
              <input
                v-model="newBatchTag"
                @keydown="handleBatchTagKeydown"
                type="text"
                placeholder="Add a tag..."
                class="tag-input"
              />
              <button @click="addBatchTag" class="btn-secondary">Add</button>
            </div>
          </div>

          <!-- Notes -->
          <div class="mb-4">
            <label class="block text-sm font-medium mb-2">Notes:</label>
            <textarea
              v-model="batchNotes"
              placeholder="What were you doing during these pings?"
              rows="3"
              class="notes-input"
            />
          </div>
        </div>

        <!-- Individual mode UI -->
        <div v-else class="individual-mode">
          <p class="text-sm text-gray-600 mb-4">
            Log each ping separately (Advanced mode - coming soon)
          </p>
          <p class="text-sm text-gray-500 italic">
            For now, please use batch mode to log all {{ pingCount }} pings at once.
          </p>
        </div>

        <!-- Missed pings summary -->
        <div class="mt-6">
          <h4 class="text-sm font-medium mb-2">Pings to log:</h4>
          <div class="ping-summary">
            <div
              v-for="ping in missedPings.slice(0, 5)"
              :key="ping.index"
              class="ping-summary-item"
            >
              <span class="text-sm">{{ formatDate(ping.time) }}</span>
              <span class="text-sm font-medium">{{ formatTime(ping.time) }}</span>
            </div>
            <div v-if="pingCount > 5" class="text-xs text-gray-500 text-center py-2">
              ... and {{ pingCount - 5 }} more
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button @click="skipAll" class="btn-secondary" :disabled="saving">
          Skip All
        </button>
        <button
          @click="saveAll"
          class="btn-primary"
          :disabled="saving || (useBatchMode && !batchTodoId)"
        >
          {{ saving ? 'Saving...' : `Log All (${pingCount})` }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.missed-pings-overlay {
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

.missed-pings-dialog {
  background: white;
  border-radius: 0.5rem;
  max-width: 700px;
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
  max-height: 200px;
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

.todo-title {
  font-weight: 500;
  color: #111827;
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
}

.ping-summary {
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  max-height: 150px;
  overflow-y: auto;
}

.ping-summary-item {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #f3f4f6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ping-summary-item:last-child {
  border-bottom: none;
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
