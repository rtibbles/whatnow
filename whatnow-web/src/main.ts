import { createApp } from 'vue'
import './assets/styles/main.css'
import App from './App.vue'
import { initDatabase } from './db/database'

// Initialize database before mounting app
initDatabase()
  .then(() => {
    createApp(App).mount('#app')
  })
  .catch((error) => {
    console.error('Failed to initialize database:', error)
    document.body.innerHTML = `
      <div style="padding: 2rem; text-align: center;">
        <h1>Failed to initialize database</h1>
        <p>${error.message}</p>
        <p>Please refresh the page to try again.</p>
      </div>
    `
  })
