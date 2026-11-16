<template>
  <div class="booking-manage-container">
    <el-card shadow="never" class="table-card">
      <div class="table-header">
        <div class="search-box">
          <el-input
            v-model="queryParams.user_name"
            placeholder="搜索申请人姓名/账号"
            clearable
            style="width: 180px"
            @keyup.enter="loadData"
          />
          <el-input
            v-model="queryParams.lab_name"
            placeholder="搜索实验室名称"
            clearable
            style="width: 180px"
            @keyup.enter="loadData"
          />
          <el-select v-model="queryParams.status" placeholder="按审批状态筛选" clearable style="width: 140px">
            <el-option label="待审核" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已驳回" value="REJECTED" />
            <el-option label="已取消" value="CANCELLED" />
          </el-select>
          <el-date-picker
            v-model="queryParams.booking_date"
            type="date"
            placeholder="按预约日期"
            value-format="YYYY-MM-DD"
            style="width: 150px"
          />
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </div>
      </div>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="user_name" label="申请人" width="130">
          <template #default="{ row }">
            <span style="font-weight: 600;">{{ row.user?.nickname || row.user?.username || row.user_name }}</span>
            <div style="font-size: 11px; color: #8c8c8c;">{{ row.user?.phone || '' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="lab_name" label="申请实验室" min-width="170">
          <template #default="{ row }">
            <span>{{ row.lab?.name || row.lab_name }}</span>
            <div style="font-size: 11px; color: #8c8c8c;">{{ row.lab?.lab_code }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="booking_date" label="预约日期" width="120" align="center" />
        <el-table-column prop="time_slot" label="预约时段" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ formatTimeSlot(row.time_slot) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="member_count" label="人数" width="70" align="center" />
        <el-table-column prop="reason" label="申请事由" min-width="160" show-overflow-tooltip />
        <el-table-column prop="status" label="审批状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="audit_remark" label="审核备注" min-width="140" show-overflow-tooltip />
        <el-table-column prop="created_at" label="申请时间" width="160" align="center" />
        <el-table-column label="审核操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'PENDING'"
              type="primary"
              size="small"
              @click="handleOpenAudit(row)"
            >
              审核审批
            </el-button>
            <el-button
              v-else
              link
              type="info"
              size="small"
              @click="handleOpenAudit(row)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.size"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 审核弹窗 -->
    <el-dialog v-model="auditDialogVisible" title="实验室预约申请审批" width="500px" destroy-on-close>
      <div v-if="currentRow" class="audit-info-summary">
        <p><strong>申请人：</strong>{{ currentRow.user?.nickname || currentRow.user_name }}</p>
        <p><strong>实验室：</strong>{{ currentRow.lab?.name || currentRow.lab_name }}</p>
        <p><strong>预约时段：</strong>{{ currentRow.booking_date }} {{ formatTimeSlot(currentRow.time_slot) }} ({{ currentRow.member_count }}人)</p>
        <p><strong>申请事由：</strong>{{ currentRow.reason }}</p>
      </div>

      <el-form :model="auditForm" label-width="90px" style="margin-top: 16px;">
        <el-form-item label="审批批注">
          <el-input
            v-model="auditForm.audit_remark"
            type="textarea"
            :rows="3"
            placeholder="请输入审批意见或驳回原因（如同意、设备冲突请更换时段等）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="auditDialogVisible = false">关闭</el-button>
          <el-button type="danger" :loading="auditSubmitting" @click="handleAuditAction('REJECTED')">
            驳回申请
          </el-button>
          <el-button type="success" :loading="auditSubmitting" @click="handleAuditAction('APPROVED')">
            审核通过
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getBookingPageApi, auditBookingApi } from '@/api/booking'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  size: 10,
  user_name: '',
  lab_name: '',
  status: '',
  booking_date: ''
})

const auditDialogVisible = ref(false)
const auditSubmitting = ref(false)
const currentRow = ref(null)

const auditForm = reactive({
  status: '',
  audit_remark: ''
})

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getBookingPageApi(queryParams)
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
  queryParams.user_name = ''
  queryParams.lab_name = ''
  queryParams.status = ''
  queryParams.booking_date = ''
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

const handleOpenAudit = (row) => {
  currentRow.value = row
  auditForm.audit_remark = row.audit_remark || ''
  auditDialogVisible.value = true
}

const handleAuditAction = async (status) => {
  if (status === 'REJECTED' && !auditForm.audit_remark.trim()) {
    ElMessage.warning('驳回申请时请填写审批批注原因')
    return
  }
  auditSubmitting.value = true
  try {
    await auditBookingApi(currentRow.value.id, {
      status,
      audit_remark: auditForm.audit_remark
    })
    ElMessage.success(status === 'APPROVED' ? '已审核通过' : '已驳回申请')
    auditDialogVisible.value = false
    loadData()
  } catch (e) {
    console.error(e)
  } finally {
    auditSubmitting.value = false
  }
}
</script>

<style scoped>
.booking-manage-container {
  display: flex;
  flex-direction: column;
}

.table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.search-box {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.audit-info-summary {
  background: #f9f9f9;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.8;
  font-size: 13px;
  color: #333;
}
</style>
