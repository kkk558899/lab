<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <div class="logo-circle">
          <el-icon :size="32" color="#67c23a"><UserFilled /></el-icon>
        </div>
        <h2 class="title">创建新账号</h2>
        <p class="subtitle">加入智能实验室预约与 Agent 协作平台</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" class="register-form" size="large">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入账号 / 学号 / 工号"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="nickname">
          <el-input
            v-model="form.nickname"
            placeholder="请输入真实姓名或昵称"
            :prefix-icon="Postcard"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码 (不少于6位)"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请确认密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="role">
          <el-select v-model="form.role" placeholder="请选择注册身份" style="width: 100%">
            <el-option label="学生 / 科研人员 (STUDENT)" value="STUDENT" />
            <el-option label="教师 / 导师 (TEACHER)" value="TEACHER" />
          </el-select>
        </el-form-item>

        <div class="register-options">
          <router-link to="/login" class="login-link">已有账号？返回登录</router-link>
        </div>

        <el-form-item>
          <el-button type="success" :loading="loading" class="submit-btn" @click="handleRegister">
            {{ loading ? '注 册 中...' : '立 即 注 册' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Postcard, UserFilled } from '@element-plus/icons-vue'
import { registerApi } from '@/api/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  nickname: '',
  password: '',
  confirmPassword: '',
  role: 'STUDENT'
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

const rules = {
  username: [{ required: true, message: '请输入用户名或学号', trigger: 'blur' }],
  nickname: [{ required: true, message: '请输入真实姓名或昵称', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }],
  role: [{ required: true, message: '请选择身份角色', trigger: 'change' }]
}

const handleRegister = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await registerApi({
        username: form.username,
        nickname: form.nickname,
        password: form.password,
        role: form.role
      })
      ElMessage.success('注册成功！正在跳转至登录页...')
      setTimeout(() => {
        router.push('/login')
      }, 1000)
    } catch (err) {
      console.error(err)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.register-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 10% 20%, rgb(43, 88, 118) 0%, rgb(78, 67, 118) 90%);
}

.register-card {
  width: 440px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2);
  padding: 36px 36px;
}

.register-header {
  text-align: center;
  margin-bottom: 24px;
}

.logo-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #f0f9eb;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
}

.title {
  font-size: 20px;
  color: #303133;
  margin-bottom: 4px;
  font-weight: 700;
}

.subtitle {
  font-size: 12px;
  color: #909399;
}

.register-options {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 20px;
}

.login-link {
  font-size: 13px;
  color: #409eff;
  text-decoration: none;
}

.login-link:hover {
  text-decoration: underline;
}

.submit-btn {
  width: 100%;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  height: 42px;
}
</style>
