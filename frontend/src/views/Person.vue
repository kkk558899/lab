<template>
  <div class="person-container">
    <el-card shadow="never" class="profile-card">
      <template #header>
        <div class="card-header">
          <span class="header-title"><el-icon><UserFilled /></el-icon> 个人资料中心</span>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="max-width: 520px; margin: 20px auto;">
        <!-- 头像上传 -->
        <el-form-item label="用户头像">
          <div class="avatar-uploader-box">
            <el-upload
              class="avatar-uploader"
              action="/api/files/upload"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleAvatarSuccess"
              :before-upload="beforeAvatarUpload"
            >
              <img v-if="form.avatar" :src="computedAvatar" class="avatar" />
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
            <div class="avatar-tip">支持 JPG / PNG / WEBP 格式，大小不超过 2MB</div>
          </div>
        </el-form-item>

        <el-form-item label="登录账号">
          <el-input v-model="form.username" disabled />
        </el-form-item>

        <el-form-item label="真实姓名" prop="nickname">
          <el-input v-model="form.nickname" placeholder="请输入真实姓名" />
        </el-form-item>

        <el-form-item label="用户角色">
          <el-tag :type="form.role === 'ADMIN' ? 'danger' : 'primary'">
            {{ form.role === 'ADMIN' ? '系统管理员' : (form.role === 'TEACHER' ? '指导教师' : '学生 / 科研人员') }}
          </el-tag>
        </el-form-item>

        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号码" />
        </el-form-item>

        <el-form-item label="电子邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入电子邮箱" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" style="width: 120px;" @click="handleSave">
            保存修改
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, UserFilled } from '@element-plus/icons-vue'
import { updateProfileApi } from '@/api/user'
import { getMeApi } from '@/api/auth'

const formRef = ref(null)
const saving = ref(false)

const form = reactive({
  id: '',
  username: '',
  nickname: '',
  role: '',
  phone: '',
  email: '',
  avatar: ''
})

const rules = {
  nickname: [{ required: true, message: '请输入姓名或昵称', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入有效的电子邮箱格式', trigger: 'blur' }]
}

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

const computedAvatar = computed(() => {
  if (!form.avatar) return ''
  if (form.avatar.startsWith('http')) return form.avatar
  return `/api${form.avatar}`
})

onMounted(async () => {
  const localUser = JSON.parse(localStorage.getItem('user') || '{}')
  Object.assign(form, localUser)

  try {
    const res = await getMeApi().catch(() => null)
    if (res && res.data) {
      Object.assign(form, res.data)
      localStorage.setItem('user', JSON.stringify(res.data))
    }
  } catch (e) {}
})

const beforeAvatarUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error('上传头像图片只能是图片格式!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('上传头像图片大小不能超过 2MB!')
    return false
  }
  return true
}

const handleAvatarSuccess = (res) => {
  if (res.code === 200 || res.code === 0) {
    form.avatar = res.data?.url || res.data || res.url
    ElMessage.success('头像上传成功')
  } else {
    ElMessage.error(res.msg || '头像上传失败')
  }
}

const handleSave = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await updateProfileApi(form)
      ElMessage.success('个人信息修改成功！')
      localStorage.setItem('user', JSON.stringify(form))
    } catch (e) {
      console.error(e)
    } finally {
      saving.value = false
    }
  })
}
</script>

<style scoped>
.person-container {
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
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

.avatar-uploader-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.avatar-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 50%;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 90px;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s;
}

.avatar-uploader:hover {
  border-color: #409eff;
}

.avatar-uploader-icon {
  font-size: 26px;
  color: #8c939d;
}

.avatar {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.avatar-tip {
  font-size: 12px;
  color: #909399;
}
</style>
