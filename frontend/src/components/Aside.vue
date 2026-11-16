<template>
  <div class="aside-container" :class="{ 'aside-collapse': isCollapse }">
    <div class="logo-box">
      <div class="logo-icon">
        <el-icon :size="24"><Cpu /></el-icon>
      </div>
      <span v-if="!isCollapse" class="logo-text">Lab Booking</span>
    </div>

    <el-menu
      :default-active="activePath"
      class="el-menu-vertical"
      :collapse="isCollapse"
      :collapse-transition="false"
      router
      background-color="#001529"
      text-color="#ffffffb3"
      active-text-color="#409eff"
    >
      <el-menu-item index="/home">
        <el-icon><HomeFilled /></el-icon>
        <template #title>系统首页</template>
      </el-menu-item>

      <el-menu-item index="/lab-list">
        <el-icon><School /></el-icon>
        <template #title>实验室大厅</template>
      </el-menu-item>

      <el-menu-item index="/ai-chat" class="ai-menu-item">
        <el-icon><Service /></el-icon>
        <template #title>
          <span>智能 AI 助手</span>
          <el-tag size="small" type="success" effect="dark" class="menu-badge">Agent</el-tag>
        </template>
      </el-menu-item>

      <el-menu-item index="/my-booking">
        <el-icon><Calendar /></el-icon>
        <template #title>我的预约</template>
      </el-menu-item>

      <!-- 管理员专区 -->
      <el-sub-menu v-if="isAdmin" index="admin-manage">
        <template #title>
          <el-icon><Management /></el-icon>
          <span>系统管理</span>
        </template>
        <el-menu-item index="/booking-manage">
          <el-icon><Tickets /></el-icon>
          <template #title>预约审核管理</template>
        </el-menu-item>
        <el-menu-item index="/lab">
          <el-icon><House /></el-icon>
          <template #title>实验室管理</template>
        </el-menu-item>
        <el-menu-item index="/device">
          <el-icon><Monitor /></el-icon>
          <template #title>实验室设备管理</template>
        </el-menu-item>
        <el-menu-item index="/user">
          <el-icon><UserFilled /></el-icon>
          <template #title>用户权限管理</template>
        </el-menu-item>
      </el-sub-menu>

      <!-- 个人中心 -->
      <el-sub-menu index="user-center">
        <template #title>
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </template>
        <el-menu-item index="/person">
          <el-icon><Postcard /></el-icon>
          <template #title>个人基本信息</template>
        </el-menu-item>
        <el-menu-item index="/password">
          <el-icon><Lock /></el-icon>
          <template #title>修改登录密码</template>
        </el-menu-item>
      </el-sub-menu>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  isCollapse: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()
const activePath = computed(() => route.path)

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch (e) {
    return {}
  }
})

const isAdmin = computed(() => {
  return user.value.role === 'ADMIN' || user.value.role === 'admin'
})
</script>

<style scoped>
.aside-container {
  height: 100vh;
  background-color: #001529;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  width: 230px;
  overflow-x: hidden;
  box-shadow: 2px 0 8px 0 rgba(29, 35, 41, 0.05);
}

.aside-collapse {
  width: 64px;
}

.logo-box {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
  background-color: #002140;
  color: #fff;
  white-space: nowrap;
}

.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #ffffff;
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}

:deep(.el-menu-item.is-active) {
  background-color: #1890ff !important;
  color: #ffffff !important;
}

.ai-menu-item {
  position: relative;
}

.menu-badge {
  margin-left: 8px;
  font-size: 10px;
  height: 18px;
  line-height: 18px;
  padding: 0 4px;
}
</style>
