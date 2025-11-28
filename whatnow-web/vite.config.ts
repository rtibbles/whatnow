/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      // Service worker will be added in Phase 9
      // strategies: 'injectManifest',
      // srcDir: 'src',
      // filename: 'service-worker.ts',
      manifest: {
        name: 'WhatNow',
        short_name: 'WhatNow',
        description: 'Activity tracking with TagTime Poisson pings',
        theme_color: '#3b82f6',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}']
      },
      devOptions: {
        enabled: true,
        type: 'module'
      }
    })
  ],
  // @ts-ignore - test config is only used by vitest
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/tests/setup.ts',
  },
  build: {
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks: {
          'rxdb': ['rxdb'],
          'vue-vendor': ['vue', '@headlessui/vue']
        }
      }
    }
  }
})
