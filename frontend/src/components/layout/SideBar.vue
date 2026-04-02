<template>
  <aside class="sidebar">
    <nav class="sidebar-nav">
      <ul class="nav-list">
        <li class="nav-item" 
            :class="{ 'active': activePage === 'workbench' }"
            @click="navigateTo('workbench')">
          <div class="nav-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/>
              <path d="M3 9H21M9 21V9H15V21" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <span class="nav-label">工作台</span>
        </li>
        
        <li class="nav-item" 
            :class="{ 'active': activePage === 'report' }"
            @click="navigateTo('report')">
          <div class="nav-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 12H15M9 16H15M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H12.5858C12.851 3 13.1054 3.10536 13.2929 3.29289L18.7071 8.70711C18.8946 8.89464 19 9.149 19 9.41421V19C19 20.1046 18.1046 21 17 21Z" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <span class="nav-label">报告</span>
        </li>
        
        <li class="nav-item" 
            :class="{ 'active': activePage === 'assistant' }"
            @click="navigateTo('assistant')">
          <div class="nav-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 12H8.01M12 12H12.01M16 12H16.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="1.5"/>
              <path d="M15 10C15 11.6569 13.6569 13 12 13C10.3431 13 9 11.6569 9 10" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <span class="nav-label">助手</span>
        </li>
      </ul>
      
      <div class="sidebar-footer">
        <div class="quick-actions">
          <button class="action-btn" @click="newProject">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="1.5"/>
            </svg>
            <span>新项目</span>
          </button>
          
          <button class="action-btn" @click="settings">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" stroke-width="1.5"/>
              <path d="M19.0765 11.0101C19.0281 10.6827 18.9998 10.3497 18.9998 10C18.9998 7.8437 18.3437 5.8333 17.1937 4.2222C17.0263 3.9877 16.7346 3.8925 16.475 4.0019C15.475 4.4019 14.5583 4.9666 13.7666 5.6666C13.5583 5.8583 13.2917 5.9499 13.025 5.9499C12.5583 5.9499 12.0917 5.7333 11.7917 5.3499C11.3917 4.8499 10.7917 4.5499 10.1583 4.5499H9.8417C9.2083 4.5499 8.6083 4.8499 8.2083 5.3499C7.9083 5.7333 7.4417 5.9499 6.975 5.9499C6.7083 5.9499 6.4417 5.8583 6.2333 5.6666C5.4417 4.9666 4.525 4.4019 3.525 4.0019C3.2654 3.8925 2.9737 3.9877 2.8063 4.2222C1.6563 5.8333 1 7.8437 1 10C1 10.3497 1.0283 10.6827 1.0765 11.0101C0.7765 11.3434 0.625 11.7668 0.625 12.2101C0.625 12.6534 0.7765 13.0768 1.0765 13.4101C1.0283 13.7375 1 14.0705 1 14.4202C1 16.5765 1.6563 18.5869 2.8063 20.198C2.9737 20.4325 3.2654 20.5277 3.525 20.4183C4.525 20.0183 5.4417 19.4536 6.2333 18.7536C6.4417 18.5619 6.7083 18.4702 6.975 18.4702C7.4417 18.4702 7.9083 18.6869 8.2083 19.1702C8.6083 19.6702 9.2083 19.9702 9.8417 19.9702H10.1583C10.7917 19.9702 11.3917 19.6702 11.7917 19.1702C12.0917 18.6869 12.5583 18.4702 13.025 18.4702C13.2917 18.4702 13.5583 18.5619 13.7666 18.7536C14.5583 19.4536 15.475 20.0183 16.475 20.4183C16.7346 20.5277 17.0263 20.4325 17.1937 20.198C18.3437 18.5869 18.9998 16.5765 18.9998 14.4202C18.9998 14.0705 18.9717 13.7375 18.9235 13.4101C19.2235 13.0768 19.375 12.6534 19.375 12.2101C19.375 11.7668 19.2235 11.3434 18.9235 11.0101C18.9717 10.6827 18.9998 10.3497 18.9998 10Z" stroke="currentColor" stroke-width="1.5"/>
            </svg>
            <span>设置</span>
          </button>
        </div>
      </div>
    </nav>
  </aside>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  activePage: {
    type: String,
    default: 'workbench'
  }
})

const emit = defineEmits(['navigate', 'new-project', 'settings'])

const navigateTo = (page) => {
  emit('navigate', page)
}

const newProject = () => {
  emit('new-project')
}

const settings = () => {
  emit('settings')
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 64px;
  bottom: 0;
  width: 280px;
  background: #f8f3ec;
  border-right: 1px solid rgba(226, 232, 240, 0.15);
  padding: 24px 0;
  display: flex;
  flex-direction: column;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 24px;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  margin: 0 12px;
  border-radius: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 0.875rem;
  color: #4a5568;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #1d1b17;
}

.nav-item.active {
  background: #ffffff;
  color: #3a2e47;
  box-shadow: 0 4px 6px rgba(58, 46, 71, 0.06);
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: currentColor;
}

.nav-label {
  flex: 1;
}

.sidebar-footer {
  margin-top: auto;
  padding: 0 12px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  border-radius: 1rem;
  background: transparent;
  border: 1px solid transparent;
  color: #4a5568;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 0.75rem;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #1d1b17;
  border-color: rgba(226, 232, 240, 0.3);
}
</style>
