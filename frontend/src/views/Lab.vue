<template>
  <div class="lab-manage-container">
    <el-card shadow="never" class="table-card">
      <div class="table-header">
        <div class="search-box">
          <el-input
            v-model="queryParams.name"
            placeholder="搜索实验室名称"
            clearable
            style="width: 200px"
            @keyup.enter="loadData"
          />
          <el-input
            v-model="queryParams.location"
            placeholder="搜索所在楼宇/位置"
            clearable
            style="width: 180px"
            @keyup.enter="loadData"
          />
          <el-select v-model="queryParams.status" placeholder="按状态筛选" clearable style="width: 140px">
            <el-option label="正常开放" :value="1" />
            <el-option label="暂停预约/维护" :value="0" />
          </el-select>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </div>

        <div class="action-box">
          <el-button type="primary" :icon="Plus" @click="handleAdd">新建实验室</el-button>
          <el-popconfirm title="确定批量删除选中的实验室吗？" @confirm="handleBatchDelete">
            <template #reference>
              <el-button type="danger" :icon="Delete" :disabled="selectedIds.length === 0">
                批量删除 ({{ selectedIds.length }})
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>

      <!-- 表格 -->
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column label="实验室封面" width="120" align="center">
          <template #default="{ row }">
            <el-image
              style="width: 80px; height: 50px; border-radius: 4px;"
              :src="formatCover(row.cover)"
              :preview-src-list="[formatCover(row.cover)]"
              fit="cover"
              preview-teleported
            >
              <template #error>
                <div class="image-slot"><el-icon><Picture /></el-icon></div>
              </template>
            </el-image>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="实验室名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="lab_code" label="房间门牌号" width="120" align="center" />
        <el-table-column prop="location" label="所在位置" min-width="140" />
        <el-table-column prop="capacity" label="容纳人数" width="100" align="center">
          <template #default="{ row }">
            <span>{{ row.capacity }} 人</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="开放状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '正常开放' : '维护中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="简介描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="170" align="center" />
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除该实验室吗？" @confirm="handleDelete(row.id)">
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
      :title="dialogType === 'add' ? '新建实验室' : '编辑实验室信息'"
      width="560px"
      destroy-on-close
    >
      <el-form ref="dialogFormRef" :model="form" :rules="dialogRules" label-width="100px">
        <el-form-item label="实验室名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：人工智能与计算视觉实验室" />
        </el-form-item>

        <el-form-item label="房间编号" prop="lab_code">
          <el-input v-model="form.lab_code" placeholder="例如：A-301" />
        </el-form-item>

        <el-form-item label="所在位置" prop="location">
          <el-input v-model="form.location" placeholder="例如：信息工程学院3楼" />
        </el-form-item>

        <el-form-item label="容纳人数" prop="capacity">
          <el-input-number v-model="form.capacity" :min="1" :max="500" style="width: 100%" />
        </el-form-item>

        <el-form-item label="开放状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">正常开放</el-radio>
            <el-radio :value="0">暂停预约 / 维护中</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="实验室封面">
          <el-upload
            class="cover-uploader"
            action="/api/files/upload"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleCoverSuccess"
          >
            <img v-if="form.cover" :src="formatCover(form.cover)" class="cover-img" />
            <el-icon v-else class="cover-uploader-icon"><Plus /></el-icon>
          </el-upload>
        </el-form-item>

        <el-form-item label="详细介绍" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="介绍实验室的主要研究方向、配备设备及安全守则"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">保存提交</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus, Delete, Edit, Picture } from '@element-plus/icons-vue'
import { getLabPageApi, addLabApi, updateLabApi, deleteLabApi, batchDeleteLabApi } from '@/api/lab'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedIds = ref([])

const queryParams = reactive({
  page: 1,
  size: 10,
  name: '',
  location: '',
  status: ''
})

const dialogVisible = ref(false)
const dialogType = ref('add')
const dialogFormRef = ref(null)
const submitLoading = ref(false)

const form = reactive({
  id: null,
  name: '',
  lab_code: '',
  location: '',
  capacity: 40,
  status: 1,
  cover: '',
  description: ''
})

const dialogRules = {
  name: [{ required: true, message: '请输入实验室名称', trigger: 'blur' }],
  lab_code: [{ required: true, message: '请输入房间编号', trigger: 'blur' }],
  location: [{ required: true, message: '请输入所在楼宇位置', trigger: 'blur' }],
  capacity: [{ required: true, message: '请输入容纳人数', trigger: 'blur' }]
}

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getLabPageApi(queryParams)
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
  queryParams.location = ''
  queryParams.status = ''
  queryParams.page = 1
  loadData()
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.map(r => r.id)
}

const formatCover = (cover) => {
  if (!cover) return ''
  if (cover.startsWith('http')) return cover
  return `/api${cover}`
}

const handleCoverSuccess = (res) => {
  if (res.code === 200 || res.code === 0) {
    form.cover = res.data?.url || res.data || res.url
    ElMessage.success('封面图片上传成功')
  } else {
    ElMessage.error(res.msg || '封面上传失败')
  }
}

const handleAdd = () => {
  dialogType.value = 'add'
  form.id = null
  form.name = ''
  form.lab_code = ''
  form.location = ''
  form.capacity = 40
  form.status = 1
  form.cover = ''
  form.description = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = () => {
  dialogFormRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (dialogType.value === 'add') {
        await addLabApi(form)
        ElMessage.success('实验室创建成功')
      } else {
        await updateLabApi(form.id, form)
        ElMessage.success('实验室修改成功')
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
    await deleteLabApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    console.error(e)
  }
}

const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) return
  try {
    await batchDeleteLabApi(selectedIds.value)
    ElMessage.success('批量删除成功')
    loadData()
  } catch (e) {
    console.error(e)
  }
}
</script>

<style scoped>
.lab-manage-container {
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

.cover-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 140px;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-uploader:hover {
  border-color: #409eff;
}

.cover-uploader-icon {
  font-size: 24px;
  color: #8c939d;
}

.cover-img {
  width: 140px;
  height: 90px;
  object-fit: cover;
  display: block;
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #909399;
}
</style>
