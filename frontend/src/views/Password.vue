<template>
  <div class="password-container">
    <el-card shadow="never" class="password-card">
      <template #header>
        <div class="card-header">
          <span class="header-title"><el-icon><Lock /></el-icon> 修改登录密码</span>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="max-width: 480px; margin: 20px auto;">
        <el-form-item label="当前原密码" prop="oldPassword">
          <el-input v-model="form.oldPassword" type="password" show-password placeholder="请输入当前旧密码" />
        </el-form-item>

        <el-form-item label="新设密码" prop="newPassword">
          <el-input v-model="form.newPassword" type="password" show-password placeholder="请输入新密码 (不少于6位)" />
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" show-password placeholder="请再次确认新密码" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 120px;" @click="handleUpdate">
            确认修改
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { updatePasswordApi } from '@/api/user'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirm = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次确认新密码'))
  } else if (value !== form.newPassword) {
    callback(new Error('两次输入的新密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirm, trigger: 'blur' }]
}

const handleUpdate = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await updatePasswordApi({
        old_password: form.oldPassword,
        new_password: form.newPassword
      })
      ElMessageBox.alert('密码已修改成功，请使用新密码重新登录！', '提示', {
        confirmButtonText: '重新登录',
        callback: () => {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          router.push('/login')
        }
      })
    } catch (err) {
      console.error(err)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.password-container {
  max-width: 800px;
  margin: 0 auto;
}

.password-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  align-items: center;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
