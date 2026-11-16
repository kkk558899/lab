<template>
  <div v-loading="loading" class="lab-detail-container">
    <div class="top-nav">
      <el-button :icon="ArrowLeft" @click="$router.back()">返回实验室列表</el-button>
    </div>

    <el-row :gutter="20" class="detail-row">
      <!-- 左侧实验室核心信息 -->
      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="detail-card">
          <div class="lab-main-header">
            <div class="lab-badge-title">
              <h2>{{ lab.name }}</h2>
              <el-tag :type="lab.status === 1 ? 'success' : 'danger'" size="large">
                {{ lab.status === 1 ? '正常开放预约' : '暂停预约/维护' }}
              </el-tag>
            </div>
            <p class="lab-subtitle"><el-icon><Location /></el-icon> {{ lab.location }} | 房间号：{{ lab.lab_code }}</p>
          </div>

          <div class="cover-image-wrapper">
            <el-image :src="formatCover(lab.cover)" fit="cover" class="cover-img" />
          </div>

          <div class="section-block">
            <h3 class="section-title"><el-icon><Document /></el-icon> 实验室简介</h3>
            <p class="description-text">
              {{ lab.description || '该实验室配备了专业软硬件实验环境，主要用于承接计算机科学、人工智能、数据工程等相关教学实验与课外科研项目。' }}
            </p>
          </div>

          <!-- 实验室设备仪器列表 -->
          <div class="section-block">
            <h3 class="section-title"><el-icon><Monitor /></el-icon> 实验室可用仪器设备</h3>
            <el-table :data="devices" border stripe style="width: 100%">
              <el-table-column prop="id" label="#" width="60" align="center" />
              <el-table-column prop="name" label="设备名称" min-width="160" />
              <el-table-column prop="model" label="型号规格" width="140" />
              <el-table-column prop="device_code" label="资产编号" width="140" />
              <el-table-column prop="status" label="设备状态" width="110" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.status === 1 ? 'success' : 'warning'">
                    {{ row.status === 1 ? '空闲可用' : '使用中' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧快速预约申请卡片 -->
      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="booking-card">
          <template #header>
            <div class="card-header">
              <span class="header-title"><el-icon><Calendar /></el-icon> 提交预约申请</span>
            </div>
          </template>

          <div class="capacity-alert">
            <el-alert
              :title="`最大容纳人数: ${lab.capacity || 40} 人 | 开放时间 08:30-21:30`"
              type="info"
              :closable="false"
              show-icon
            />
          </div>

          <el-form ref="formRef" :model="form" :rules="rules" label-position="top" style="margin-top: 16px;">
            <el-form-item label="预约日期" prop="booking_date">
              <el-date-picker
                v-model="form.booking_date"
                type="date"
                placeholder="请选择预约日期"
                value-format="YYYY-MM-DD"
                :disabled-date="disabledDate"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="预约时间段" prop="time_slot">
              <el-radio-group v-model="form.time_slot" style="width: 100%; display: flex; flex-direction: column; gap: 8px;">
                <el-radio value="MORNING" border style="margin-right: 0; width: 100%;">上午 (08:30 - 12:00)</el-radio>
                <el-radio value="AFTERNOON" border style="margin-right: 0; width: 100%;">下午 (13:30 - 17:30)</el-radio>
                <el-radio value="EVENING" border style="margin-right: 0; width: 100%;">晚上 (18:30 - 21:30)</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="拟使用人数" prop="member_count">
              <el-input-number v-model="form.member_count" :min="1" :max="lab.capacity || 50" style="width: 100%" />
            </el-form-item>

            <el-form-item label="实验目的与事由" prop="reason">
              <el-input
                v-model="form.reason"
                type="textarea"
                :rows="3"
                placeholder="请说明预约用途、所属课程或实验主题"
              />
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              :loading="submitting"
              :disabled="lab.status !== 1"
              style="width: 100%; margin-top: 10px;"
              @click="handleSubmitBooking"
            >
              {{ lab.status === 1 ? '确认提交预约' : '实验室维护中暂不可约' }}
            </el-button>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Location, Document, Monitor, Calendar } from '@element-plus/icons-vue'
import { getLabByIdApi } from '@/api/lab'
import { getDevicesByLabIdApi } from '@/api/device'
import { createBookingApi } from '@/api/booking'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const lab = ref({})
const devices = ref([])

const form = reactive({
  lab_id: null,
  booking_date: '',
  time_slot: 'AFTERNOON',
  member_count: 1,
  reason: ''
})

const rules = {
  booking_date: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
  time_slot: [{ required: true, message: '请选择时间段', trigger: 'change' }],
  reason: [{ required: true, message: '请输入实验事由', trigger: 'blur' }]
}

const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7
}

onMounted(async () => {
  const labId = route.params.id
  form.lab_id = labId
  loading.value = true
  try {
    const res = await getLabByIdApi(labId)
    if (res && res.data) {
      lab.value = res.data
    }
    const devRes = await getDevicesByLabIdApi(labId).catch(() => null)
    if (devRes && devRes.data) {
      devices.value = devRes.data
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const formatCover = (cover) => {
  if (!cover) return 'https://images.unsplash.com/photo-1581093458791-9f3c3900df4b?w=1000&q=80'
  if (cover.startsWith('http')) return cover
  return `/api${cover}`
}

const handleSubmitBooking = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await createBookingApi(form)
      ElMessage.success('预约申请已提交成功！')
      router.push('/my-booking')
    } catch (e) {
      console.error(e)
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.lab-detail-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.top-nav {
  margin-bottom: 4px;
}

.detail-card, .booking-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.lab-main-header {
  margin-bottom: 16px;
}

.lab-badge-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.lab-badge-title h2 {
  font-size: 22px;
  font-weight: 700;
  color: #1f1f1f;
}

.lab-subtitle {
  font-size: 13px;
  color: #8c8c8c;
  display: flex;
  align-items: center;
  gap: 4px;
}

.cover-image-wrapper {
  width: 100%;
  height: 260px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.cover-img {
  width: 100%;
  height: 100%;
}

.section-block {
  margin-top: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.description-text {
  font-size: 14px;
  color: #595959;
  line-height: 1.8;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
