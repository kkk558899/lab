<template>
  <div class="device-manage-container">
    <el-card shadow="never" class="table-card">
      <div class="table-header">
        <div class="search-box">
          <el-input
            v-model="queryParams.name"
            placeholder="搜索设备仪器名称"
            clearable
            style="width: 200px"
            @keyup.enter="loadData"
          />
          <el-select v-model="queryParams.lab_id" placeholder="按所属实验室筛选" clearable style="width: 200px">
            <el-option
              v-for="lab in labOptions"
              :key="lab.id"
              :label="lab.name"
              :value="lab.id"
            />
          </el-select>
          <el-select v-model="queryParams.status" placeholder="按设备状态筛选" clearable style="width: 140px">
            <el-option label="正常可用" :value="1" />
            <el-option label="使用中" :value="2" />
            <el-option label="维修维护" :value="0" />
            <el-option label="已报废" :value="-1" />
          </el-select>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </div>

        <div class="action-box">
          <el-button type="primary" :icon="Plus" @click="handleAdd">登记新设备</el-button>
        </div>
      </div>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="设备名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="device_code" label="设备编号 / 资产号" width="160" />
        <el-table-column prop="model" label="规格型号" width="140" />
        <el-table-column prop="lab_name" label="所属实验室" min-width="160">
          <template #default="{ row }">
            <el-tag type="info">{{ row.lab?.name || row.lab_name || '未分配' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="当前状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="purchase_date" label="购置日期" width="130" align="center" />
        <el-table-column prop="description" label="备注说明" min-width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除该设备记录吗？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger" size="small" :icon="Delete">删除</el-button>
              </template>
            </el-popconfirm>
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

    <!-- 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '登记新设备' : '编辑设备信息'"
      width="520px"
      destroy-on-close
    >
      <el-form ref="dialogFormRef" :model="form" :rules="dialogRules" label-width="100px">
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：NVIDIA RTX 4090 深度学习计算工作站" />
        </el-form-item>

        <el-form-item label="设备编号" prop="device_code">
          <el-input v-model="form.device_code" placeholder="例如：EQ-AI-2026-001" />
        </el-form-item>

        <el-form-item label="规格型号" prop="model">
          <el-input v-model="form.model" placeholder="例如：Dell Precision 7920" />
        </el-form-item>

        <el-form-item label="所属实验室" prop="lab_id">
          <el-select v-model="form.lab_id" placeholder="请选择归属实验室" style="width: 100%">
            <el-option
              v-for="lab in labOptions"
              :key="lab.id"
              :label="lab.name"
              :value="lab.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="设备状态" prop="status">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="正常可用" :value="1" />
            <el-option label="使用中 / 占用" :value="2" />
            <el-option label="故障检修 / 维护" :value="0" />
            <el-option label="已报废" :value="-1" />
          </el-select>
        </el-form-item>

        <el-form-item label="购置日期" prop="purchase_date">
          <el-date-picker
            v-model="form.purchase_date"
            type="date"
            placeholder="选择购置日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="备注说明" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="设备相关配置参数、注意事项" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确认提交</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus, Delete, Edit } from '@element-plus/icons-vue'
import { getDevicePageApi, addDeviceApi, updateDeviceApi, deleteDeviceApi } from '@/api/device'
import { getLabListApi } from '@/api/lab'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const labOptions = ref([])

const queryParams = reactive({
  page: 1,
  size: 10,
  name: '',
  lab_id: '',
  status: ''
})

const dialogVisible = ref(false)
const dialogType = ref('add')
const dialogFormRef = ref(null)
const submitLoading = ref(false)

const form = reactive({
  id: null,
  name: '',
  device_code: '',
  model: '',
  lab_id: null,
  status: 1,
  purchase_date: '',
  description: ''
})

const dialogRules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  device_code: [{ required: true, message: '请输入设备编号', trigger: 'blur' }],
  lab_id: [{ required: true, message: '请选择归属实验室', trigger: 'change' }]
}

onMounted(() => {
  loadLabs()
  loadData()
})

const loadLabs = async () => {
  try {
    const res = await getLabListApi()
    if (res && res.data) {
      labOptions.value = res.data
    }
  } catch (e) {}
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getDevicePageApi(queryParams)
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
  queryParams.name = ''
  queryParams.lab_id = ''
  queryParams.status = ''
  queryParams.page = 1
  loadData()
}

const getStatusTag = (status) => {
  if (status === 1) return 'success'
  if (status === 2) return 'warning'
  if (status === 0) return 'danger'
  return 'info'
}

const getStatusText = (status) => {
  if (status === 1) return '正常可用'
  if (status === 2) return '使用中'
  if (status === 0) return '维修维护'
  return '已报废'
}

const handleAdd = () => {
  dialogType.value = 'add'
  form.id = null
  form.name = ''
  form.device_code = ''
  form.model = ''
  form.lab_id = labOptions.value[0]?.id || null
  form.status = 1
  form.purchase_date = ''
  form.description = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  Object.assign(form, row)
  form.lab_id = row.lab_id || row.lab?.id
  dialogVisible.value = true
}

const handleSubmit = () => {
  dialogFormRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (dialogType.value === 'add') {
        await addDeviceApi(form)
        ElMessage.success('设备录入成功')
      } else {
        await updateDeviceApi(form.id, form)
        ElMessage.success('设备更新成功')
      }
      dialogVisible.value = false
      loadData()
    } catch (e) {
      console.error(e)
    } finally {
      submitLoading.value = false
    }
  })
}

const handleDelete = async (id) => {
  try {
    await deleteDeviceApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    console.error(e)
  }
}
</script>

<style scoped>
.device-manage-container {
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

.action-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
