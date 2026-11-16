<template>
  <div class="user-manage-container">
    <el-card shadow="never" class="table-card">
      <!-- 搜索筛选栏 -->
      <div class="table-header">
        <div class="search-box">
          <el-input
            v-model="queryParams.username"
            placeholder="按用户名 / 学号搜索"
            clearable
            style="width: 200px"
            @keyup.enter="loadData"
          />
          <el-input
            v-model="queryParams.nickname"
            placeholder="按真实姓名搜索"
            clearable
            style="width: 180px"
            @keyup.enter="loadData"
          />
          <el-select v-model="queryParams.role" placeholder="按角色筛选" clearable style="width: 160px">
            <el-option label="管理员 (ADMIN)" value="ADMIN" />
            <el-option label="教师 (TEACHER)" value="TEACHER" />
            <el-option label="学生 (STUDENT)" value="STUDENT" />
          </el-select>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </div>

        <div class="action-box">
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增用户</el-button>
          <el-popconfirm title="确定批量删除选中的用户吗？" @confirm="handleBatchDelete">
            <template #reference>
              <el-button type="danger" :icon="Delete" :disabled="selectedIds.length === 0">
                批量删除 ({{ selectedIds.length }})
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>

      <!-- 数据表格 -->
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
        <el-table-column label="头像" width="70" align="center">
          <template #default="{ row }">
            <el-avatar :size="36" :src="formatAvatar(row.avatar)">
              {{ row.nickname?.charAt(0) || row.username?.charAt(0) }}
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="登录账号" min-width="120" />
        <el-table-column prop="nickname" label="真实姓名" min-width="120" />
        <el-table-column prop="role" label="身份角色" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="getRoleTag(row.role)">{{ getRoleName(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系电话" min-width="130" />
        <el-table-column prop="email" label="电子邮箱" min-width="160" />
        <el-table-column prop="created_at" label="注册时间" width="170" align="center" />
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除该用户吗？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger" size="small" :icon="Delete">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页器 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 新增 / 编辑用户弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增用户' : '编辑用户信息'"
      width="500px"
      destroy-on-close
    >
      <el-form ref="dialogFormRef" :model="form" :rules="dialogRules" label-width="90px">
        <el-form-item label="登录账号" prop="username">
          <el-input v-model="form.username" :disabled="dialogType === 'edit'" placeholder="请输入登录账号/学号" />
        </el-form-item>

        <el-form-item v-if="dialogType === 'add'" label="初始密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入初始密码" />
        </el-form-item>

        <el-form-item label="真实姓名" prop="nickname">
          <el-input v-model="form.nickname" placeholder="请输入真实姓名" />
        </el-form-item>

        <el-form-item label="身份角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="系统管理员 (ADMIN)" value="ADMIN" />
            <el-option label="指导教师 (TEACHER)" value="TEACHER" />
            <el-option label="学生 / 科研人员 (STUDENT)" value="STUDENT" />
          </el-select>
        </el-form-item>

        <el-form-item label="手机号码" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
        </el-form-item>

        <el-form-item label="电子邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入电子邮箱" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定提交</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus, Delete, Edit } from '@element-plus/icons-vue'
import { getUserPageApi, addUserApi, updateUserApi, deleteUserApi, batchDeleteUserApi } from '@/api/user'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedIds = ref([])

const queryParams = reactive({
  page: 1,
  size: 10,
  username: '',
  nickname: '',
  role: ''
})

const dialogVisible = ref(false)
const dialogType = ref('add')
const dialogFormRef = ref(null)
const submitLoading = ref(false)

const form = reactive({
  id: null,
  username: '',
  password: '',
  nickname: '',
  role: 'STUDENT',
  phone: '',
  email: ''
})

const dialogRules = {
  username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入初始密码', trigger: 'blur' }],
  nickname: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getUserPageApi(queryParams)
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
  queryParams.username = ''
  queryParams.nickname = ''
  queryParams.role = ''
  queryParams.page = 1
  loadData()
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.map(r => r.id)
}

const formatAvatar = (avatar) => {
  if (!avatar) return ''
  if (avatar.startsWith('http')) return avatar
  return `/api${avatar}`
}

const getRoleTag = (role) => {
  if (role === 'ADMIN') return 'danger'
  if (role === 'TEACHER') return 'warning'
  return 'primary'
}

const getRoleName = (role) => {
  if (role === 'ADMIN') return '管理员'
  if (role === 'TEACHER') return '教师'
  return '学生'
}

const handleAdd = () => {
  dialogType.value = 'add'
  form.id = null
  form.username = ''
  form.password = '123456'
  form.nickname = ''
  form.role = 'STUDENT'
  form.phone = ''
  form.email = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  form.id = row.id
  form.username = row.username
  form.nickname = row.nickname
  form.role = row.role
  form.phone = row.phone
  form.email = row.email
  dialogVisible.value = true
}

const handleSubmit = () => {
  dialogFormRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (dialogType.value === 'add') {
        await addUserApi(form)
        ElMessage.success('用户创建成功')
      } else {
        await updateUserApi(form.id, form)
        ElMessage.success('用户更新成功')
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
    await deleteUserApi(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    console.error(e)
  }
}

const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) return
  try {
    await batchDeleteUserApi(selectedIds.value)
    ElMessage.success('批量删除成功')
    loadData()
  } catch (e) {
    console.error(e)
  }
}
</script>

<style scoped>
.user-manage-container {
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
