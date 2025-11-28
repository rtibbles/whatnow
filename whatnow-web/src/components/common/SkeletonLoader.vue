<template>
  <div
    class="animate-pulse"
    :class="containerClass"
  >
    <div
      v-if="type === 'text'"
      class="h-4 bg-gray-200 rounded"
      :class="[widthClass, heightClass]"
    ></div>

    <div
      v-else-if="type === 'circle'"
      class="bg-gray-200 rounded-full"
      :class="[widthClass, heightClass]"
    ></div>

    <div
      v-else-if="type === 'rectangle'"
      class="bg-gray-200 rounded"
      :class="[widthClass, heightClass]"
    ></div>

    <div
      v-else-if="type === 'card'"
      class="bg-white rounded-lg border border-gray-200 p-6"
    >
      <div class="space-y-4">
        <div class="h-4 bg-gray-200 rounded w-3/4"></div>
        <div class="h-4 bg-gray-200 rounded w-full"></div>
        <div class="h-4 bg-gray-200 rounded w-5/6"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  type?: 'text' | 'circle' | 'rectangle' | 'card';
  width?: string;
  height?: string;
  containerClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  width: 'full',
  height: '4',
  containerClass: ''
});

const widthClass = computed(() => {
  if (props.width.startsWith('w-')) return props.width;
  return `w-${props.width}`;
});

const heightClass = computed(() => {
  if (props.height.startsWith('h-')) return props.height;
  return `h-${props.height}`;
});
</script>
