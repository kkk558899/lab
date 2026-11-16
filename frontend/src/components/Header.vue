<template>
  <div class="header-container">
    <div class="header-left">
      <div class="toggle-btn" @click="$emit('toggle-collapse')">
        <el-icon :size="20">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </div>
      <div class="system-title">
        <el-icon class="title-icon"><Platform /></el-icon>
        <span>智能实验室预约系统</span>
      </div>
    </div>

    <div class="header-right">
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user-info">
          <el-avatar :size="34" :src="userAvatar">
            <el-icon><UserFilled /></el-icon>
          </el-avatar>
          <span class="username">{{ user.nickname || user.username || '用户' }}</span>
          <el-tag size="small" :type="user.role === 'ADMIN' ? 'danger' : 'primary'" class="role-tag">
            {{ user.role === 'ADMIN' ? '管理员' : '学生/教师' }}
          </el-tag>
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon> 个人信息
            </el-dropdown-item>
            <el-dropdown-item command="password">
              <el-icon><Lock /></el-icon> 修改密码
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  isCollapse: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle-collapse'])

const router = useRouter()

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch (e) {
    return {}
  }
})

const userAvatar = computed(() => {
  if (user.value.avatar) {
    if (user.value.avatar.startsWith('http')) return user.value.avatar
    return `/api${user.value.avatar}`
  }
  return ''
})

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/person')
  } else if (command === 'password') {
    router.push('/password')
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出当前系统吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      ElMessage.success('已安全退出登录')
      router.push('/login')
    }).catch(() => {})
  }
}
</script>

<style scoped>
.header-container {
  height: 60px;
  background-color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  position: relative;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toggle-btn {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  transition: background 0.2s;
  color: #606266;
}

.toggle-btn:hover {
  background-color: #f2f3f5;
  color: #409eff;
}

.system-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  gap: 8px;
  letter-spacing: 0.5px;
}

.title-icon {
  font-size: 22px;
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: 10px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.role-tag {
  font-size: 11px;
}
</style>
