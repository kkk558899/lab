<template>
  <div class="lab-list-container">
    <!-- 头部搜索筛选 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-header">
        <div class="filter-title">
          <h2><el-icon><School /></el-icon> 实验室预约大厅</h2>
          <p class="sub">选择您所需的实验室进行排期查看与在线预约申请</p>
        </div>
        <div class="search-inputs">
          <el-input
            v-model="queryParams.name"
            placeholder="按实验室名称 / 编号搜索"
            clearable
            style="width: 240px"
            :prefix-icon="Search"
            @keyup.enter="loadData"
          />
          <el-input
            v-model="queryParams.location"
            placeholder="按楼宇位置搜索"
            clearable
            style="width: 180px"
            :prefix-icon="Location"
            @keyup.enter="loadData"
          />
          <el-button type="primary" :icon="Search" @click="loadData">搜索实验室</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </div>
      </div>
    </el-card>

    <!-- 实验室卡片列表网格 -->
    <div v-loading="loading" class="lab-cards-grid">
      <div v-for="lab in labList" :key="lab.id" class="lab-card">
        <div class="lab-cover-box" :style="{ backgroundImage: `url(${formatCover(lab.cover)})` }">
          <div class="cover-overlay">
            <el-tag :type="lab.status === 1 ? 'success' : 'danger'" effect="dark" class="status-badge">
              {{ lab.status === 1 ? '开放预约' : '暂停预约' }}
            </el-tag>
            <div class="lab-code-badge">{{ lab.lab_code }}</div>
          </div>
        </div>

        <div class="lab-card-body">
          <h3 class="lab-card-title">{{ lab.name }}</h3>
          
          <div class="lab-info-items">
            <div class="info-item">
              <el-icon><Location /></el-icon>
              <span>{{ lab.location }}</span>
            </div>
            <div class="info-item">
              <el-icon><User /></el-icon>
              <span>容纳人数：{{ lab.capacity }} 人</span>
            </div>
            <div class="info-item">
              <el-icon><Monitor /></el-icon>
              <span>关联设备：{{ lab.device_count || '多台高配仪器' }}</span>
            </div>
          </div>

          <p class="lab-desc">{{ lab.description || '提供高规格计算资源与实验环境，欢迎师生预约开展教学与科研实验。' }}</p>

          <div class="card-action-footer">
            <el-button link type="primary" @click="handleViewDetail(lab.id)">
              查看详情 <el-icon><ArrowRight /></el-icon>
            </el-button>
            <el-button
              type="primary"
              :disabled="lab.status !== 1"
              @click="handleOpenBooking(lab)"
            >
              <el-icon><Calendar /></el-icon> 立即预约
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.size"
        :total="total"
        layout="total, prev, pager, next, jumper"
        @current-change="loadData"
      />
    </div>

    <!-- 快速预约弹窗 -->
    <el-dialog v-model="bookingDialogVisible" title="提交实验室预约申请" width="540px" destroy-on-close>
      <el-form ref="bookingFormRef" :model="bookingForm" :rules="bookingRules" label-width="100px">
        <el-form-item label="所选实验室">
          <el-input :model-value="`${currentLab.name} (${currentLab.lab_code})`" disabled />
        </el-form-item>

        <el-form-item label="预约日期" prop="booking_date">
          <el-date-picker
            v-model="bookingForm.booking_date"
            type="date"
            placeholder="请选择预约日期"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="预约时间段" prop="time_slot">
          <el-select v-model="bookingForm.time_slot" placeholder="请选择时间段" style="width: 100%">
            <el-option label="上午 (08:30 - 12:00)" value="MORNING" />
            <el-option label="下午 (13:30 - 17:30)" value="AFTERNOON" />
            <el-option label="晚上 (18:30 - 21:30)" value="EVENING" />
          </el-select>
        </el-form-item>

        <el-form-item label="使用人数" prop="member_count">
          <el-input-number v-model="bookingForm.member_count" :min="1" :max="currentLab.capacity || 50" style="width: 100%" />
        </el-form-item>

        <el-form-item label="申请事由" prop="reason">
          <el-input
            v-model="bookingForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请详细描述实验项目内容、课程名称或科研目的"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="bookingDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="bookingSubmitting" @click="handleConfirmBooking">
            提交申请
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, School, Location, User, Monitor, Calendar, ArrowRight } from '@element-plus/icons-vue'
import { getLabPageApi } from '@/api/lab'
import { createBookingApi } from '@/api/booking'

const router = useRouter()
const loading = ref(false)
const labList = ref([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  size: 8,
  name: '',
  location: ''
})

const bookingDialogVisible = ref(false)
const bookingSubmitting = ref(false)
const bookingFormRef = ref(null)
const currentLab = ref({})

const bookingForm = reactive({
  lab_id: null,
  booking_date: '',
  time_slot: 'AFTERNOON',
  member_count: 1,
  reason: ''
})

const bookingRules = {
  booking_date: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
  time_slot: [{ required: true, message: '请选择预约时间段', trigger: 'change' }],
  reason: [{ required: true, message: '请输入申请事由', trigger: 'blur' }]
}

const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7
}

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getLabPageApi(queryParams)
    if (res && res.data) {
      labList.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const resetQuery = () => {
  queryParams.name = ''
  queryParams.location = ''
  queryParams.page = 1
  loadData()
}

const formatCover = (cover) => {
  if (!cover) return 'https://images.unsplash.com/photo-1581093458791-9f3c3900df4b?w=600&q=80'
  if (cover.startsWith('http')) return cover
  return `/api${cover}`
}

const handleViewDetail = (id) => {
  router.push(`/lab-detail/${id}`)
}

const handleOpenBooking = (lab) => {
  currentLab.value = lab
  bookingForm.lab_id = lab.id
  bookingForm.booking_date = ''
  bookingForm.time_slot = 'AFTERNOON'
  bookingForm.member_count = 1
  bookingForm.reason = ''
  bookingDialogVisible.value = true
}

const handleConfirmBooking = () => {
  bookingFormRef.value.validate(async (valid) => {
    if (!valid) return
    bookingSubmitting.value = true
    try {
      await createBookingApi(bookingForm)
      ElMessage.success('预约申请已提交，请等待管理员审核')
      bookingDialogVisible.value = false
      router.push('/my-booking')
    } catch (e) {
      console.error(e)
    } finally {
      bookingSubmitting.value = false
    }
  })
}
</script>

<style scoped>
.lab-list-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-title h2 {
  font-size: 20px;
  font-weight: 700;
  color: #262626;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.sub {
  font-size: 13px;
  color: #8c8c8c;
}

.search-inputs {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.lab-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.lab-card {
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: flex;
  flex-direction: column;
}

.lab-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.09);
}

.lab-cover-box {
  height: 160px;
  background-size: cover;
  background-position: center;
  position: relative;
}

.cover-overlay {
  position: absolute;
  top: 10px;
  left: 10px;
  right: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.lab-code-badge {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.lab-card-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.lab-card-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f1f1f;
  margin-bottom: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lab-info-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #595959;
}

.lab-desc {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.5;
  height: 36px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 16px;
}

.card-action-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 10px;
}
</style>
