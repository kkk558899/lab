<template>
  <div class="my-booking-container">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="header-title"><el-icon><Calendar /></el-icon> 我的实验室预约记录</span>
          <el-button type="primary" :icon="Plus" @click="$router.push('/lab-list')">前往预约实验室</el-button>
        </div>
      </template>

      <!-- 搜索筛选 -->
      <div class="table-header">
        <div class="search-box">
          <el-select v-model="queryParams.status" placeholder="按审批状态筛选" clearable style="width: 160px">
            <el-option label="待审核" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已驳回" value="REJECTED" />
            <el-option label="已取消" value="CANCELLED" />
          </el-select>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </div>
      </div>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="预约编号" width="90" align="center" />
        <el-table-column prop="lab_name" label="预约实验室" min-width="180">
          <template #default="{ row }">
            <span style="font-weight: 600;">{{ row.lab?.name || row.lab_name }}</span>
            <div style="font-size: 12px; color: #8c8c8c;">{{ row.lab?.location || row.location }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="booking_date" label="预约日期" width="130" align="center" />
        <el-table-column prop="time_slot" label="预约时间段" width="130" align="center">
          <template #default="{ row }">
            <el-tag>{{ formatTimeSlot(row.time_slot) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="member_count" label="使用人数" width="90" align="center" />
        <el-table-column prop="reason" label="申请事由" min-width="180" show-overflow-tooltip />
        <el-table-column prop="status" label="审批状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="audit_remark" label="审核批注" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.audit_remark">{{ row.audit_remark }}</span>
            <span v-else style="color: #bfbfbf;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="160" align="center" />
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-popconfirm
              v-if="row.status === 'PENDING' || row.status === 'APPROVED'"
              title="确定要取消该条预约申请吗？"
              @confirm="handleCancel(row.id)"
            >
              <template #reference>
                <el-button link type="danger" size="small">取消预约</el-button>
              </template>
            </el-popconfirm>
            <span v-else style="color: #bfbfbf; font-size: 12px;">无操作</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Calendar, Plus, Search, Refresh } from '@element-plus/icons-vue'
import { getMyBookingsApi, cancelBookingApi } from '@/api/booking'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  size: 10,
  status: ''
})

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getMyBookingsApi(queryParams)
    if (res && res.data) {
      tableData.value = res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const resetQuery = () => {
  queryParams.status = ''
  queryParams.page = 1
  loadData()
}

const formatTimeSlot = (slot) => {
  if (slot === 'MORNING') return '上午 (08:30-12:00)'
  if (slot === 'AFTERNOON') return '下午 (13:30-17:30)'
  if (slot === 'EVENING') return '晚上 (18:30-21:30)'
  return slot || '-'
}

const getStatusTag = (status) => {
  if (status === 'PENDING') return 'warning'
  if (status === 'APPROVED') return 'success'
  if (status === 'REJECTED') return 'danger'
  return 'info'
}

const getStatusText = (status) => {
  if (status === 'PENDING') return '待审核'
  if (status === 'APPROVED') return '已通过'
  if (status === 'REJECTED') return '已驳回'
  if (status === 'CANCELLED') return '已取消'
  return status || '-'
}

const handleCancel = async (id) => {
  try {
    await cancelBookingApi(id)
    ElMessage.success('预约已取消')
    loadData()
  } catch (e) {
    console.error(e)
  }
}
</script>

<style scoped>
.my-booking-container {
  display: flex;
  flex-direction: column;
}

.table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
