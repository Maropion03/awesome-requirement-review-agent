<template>
  <header class="top-navigation">
    <div class="nav-container">
      <div class="nav-brand">
        <div class="logo">PRD Review Workbench</div>
      </div>
      
      <div class="nav-center">
        <div class="project-info">
          <span class="current-project">{{ currentProject }}</span>
        </div>
      </div>
      
      <div class="nav-actions">
        <button class="nav-button help-btn" @click="showHelp">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 10C10 8.34315 11.3431 7 13 7C14.6569 7 16 8.34315 16 10C16 11.6569 14.6569 13 13 13M13 13V16M12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21Z" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span>帮助</span>
        </button>
        
        <div class="user-menu">
          <div class="user-avatar">
            <span>{{ userInitials }}</span>
          </div>
          <span class="user-name">{{ userName }}</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'

const props = defineProps({
  currentProject: {
    type: String,
    default: '未选择项目'
  },
  userName: {
    type: String,
    default: '用户'
  },
  userInitials: {
    type: String,
    default: 'U'
  }
})

const emit = defineEmits(['help-clicked'])

const showHelp = () => {
  emit('help-clicked')
}
</script>

<style scoped>
.top-navigation {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: #f8f3ec;
  border-bottom: 1px solid rgba(226, 232, 240, 0.15);
  box-shadow: 0 4px 6px rgba(31, 24, 23, 0.06);
  height: 64px;
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 24px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  font-family: 'Satoshi', 'Inter', sans-serif;
  font-weight: 700;
  font-size: 1.125rem;
  color: #1d1b17;
  letter-spacing: -0.02em;
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 16px;
}

.current-project {
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 0.875rem;
  color: #4a5568;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 9999px;
  background: #ffffff;
  border: 1px solid transparent;
  color: #1d1b17;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 0.875rem;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #3a2e47;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.75rem;
}

.user-name {
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 0.875rem;
  color: #1d1b17;
}
</style>
