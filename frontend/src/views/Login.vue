<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-circle">
          <el-icon :size="32" color="#409eff"><Cpu /></el-icon>
        </div>
        <h2 class="title">智能实验室预约系统</h2>
        <p class="subtitle">Smart Laboratory Reservation & Agent System</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" class="login-form" size="large">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入账号 / 学号"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <div class="login-options">
          <el-checkbox v-model="rememberMe">记住账号</el-checkbox>
          <router-link to="/register" class="register-link">还没有账号？立即注册</router-link>
        </div>

        <el-form-item>
          <el-button type="primary" :loading="loading" class="submit-btn" @click="handleLogin">
            {{ loading ? '登 录 中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Cpu } from '@element-plus/icons-vue'
import { loginApi } from '@/api/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const rememberMe = ref(true)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名或学号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

onMounted(() => {
  const savedUser = localStorage.getItem('saved_username')
  if (savedUser) {
    form.username = savedUser
  }
})

const handleLogin = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await loginApi(form)
      ElMessage.success('登录成功！欢迎使用系统')
      // 存储 token 和用户信息
      const data = res.data || res
      localStorage.setItem('token', data.token || data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user || data))
      
      if (rememberMe.value) {
        localStorage.setItem('saved_username', form.username)
      } else {
        localStorage.removeItem('saved_username')
      }

      router.push('/home')
    } catch (err) {
      console.error(err)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1f4037 0%, #99f2c8 100%);
  background: radial-gradient(circle at 10% 20%, rgb(43, 88, 118) 0%, rgb(78, 67, 118) 90%);
}

.login-card {
  width: 420px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2);
  padding: 40px 36px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #ecf5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}

.title {
  font-size: 22px;
  color: #303133;
  margin-bottom: 6px;
  font-weight: 700;
}

.subtitle {
  font-size: 12px;
  color: #909399;
}

.login-form {
  margin-top: 20px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 22px;
}

.register-link {
  font-size: 13px;
  color: #409eff;
  text-decoration: none;
}

.register-link:hover {
  text-decoration: underline;
}

.submit-btn {
  width: 100%;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  height: 44px;
}
</style>
