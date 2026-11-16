<template>
  <div class="home-container">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-left">
        <h1 class="greeting">欢迎回来，{{ user.nickname || user.username || '同学' }} 👋</h1>
        <p class="desc">今日开放实验室运行正常，支持通过 AI 智能助手进行自然语言预约与规则咨询。</p>
      </div>
      <div class="banner-right">
        <el-button type="primary" size="large" round @click="$router.push('/ai-chat')">
          <el-icon><Service /></el-icon> AI 智能预约助手
        </el-button>
        <el-button size="large" round @click="$router.push('/lab-list')">
          <el-icon><School /></el-icon> 浏览实验室
        </el-button>
      </div>
    </div>

    <!-- 核心数据指标统计 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-blue">
          <div class="stat-icon-wrapper">
            <el-icon :size="28"><House /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-title">实验室总数</div>
            <div class="stat-value">{{ stats.lab_count || 12 }} <span class="unit">间</span></div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-green">
          <div class="stat-icon-wrapper">
            <el-icon :size="28"><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-title">实验仪器设备</div>
            <div class="stat-value">{{ stats.device_count || 86 }} <span class="unit">台/套</span></div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-orange">
          <div class="stat-icon-wrapper">
            <el-icon :size="28"><Calendar /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-title">累计预约人次</div>
            <div class="stat-value">{{ stats.booking_count || 328 }} <span class="unit">次</span></div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-purple">
          <div class="stat-icon-wrapper">
            <el-icon :size="28"><Tickets /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-title">待审核申请</div>
            <div class="stat-value">{{ stats.pending_count || 5 }} <span class="unit">条</span></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 下半部分功能区 -->
    <el-row :gutter="20" class="content-row">
      <!-- 快捷预约推荐与快速入口 -->
      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="card-header">
              <span class="header-title"><el-icon><Compass /></el-icon> 热门实验室推荐</span>
              <el-button link type="primary" @click="$router.push('/lab-list')">查看全部 <el-icon><ArrowRight /></el-icon></el-button>
            </div>
          </template>
          <div class="lab-grid">
            <div v-for="lab in hotLabs" :key="lab.id" class="hot-lab-item" @click="handleGoLab(lab.id)">
              <div class="lab-cover" :style="{ backgroundImage: `url(${lab.cover || '/lab-default.png'})` }">
                <el-tag size="small" :type="lab.status === 1 ? 'success' : 'danger'" class="status-tag">
                  {{ lab.status === 1 ? '开放预约' : '维护中' }}
                </el-tag>
              </div>
              <div class="lab-detail">
                <div class="lab-name">{{ lab.name }}</div>
                <div class="lab-meta"><el-icon><Location /></el-icon> {{ lab.location }}</div>
                <div class="lab-capacity"><el-icon><UserFilled /></el-icon> 容纳人数: {{ lab.capacity }} 人</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 系统近期公告与使用规范 -->
        <el-card shadow="never" class="section-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span class="header-title"><el-icon><Bell /></el-icon> 实验室安全守则与预约须知</span>
            </div>
          </template>
          <el-collapse v-model="activeCollapse">
            <el-collapse-item title="1. 预约开放时间与审批流程" name="1">
              <div>常规实验室开放时间为每日 08:30 - 21:30。学生需提前至少 1 天提交预约申请，由实验室管理员审核通过后方可进入。</div>
            </el-collapse-item>
            <el-collapse-item title="2. 智能 AI 助手快速排期指引" name="2">
              <div>您可以在「智能 AI 助手」中直接输入类似 <i>“我想预约明天下午的人工智能实验室 3 号机房”</i>，Agent 会自动帮您校验排期与自动填单。</div>
            </el-collapse-item>
            <el-collapse-item title="3. 实验室设备与安全管理规章" name="3">
              <div>使用贵重精密仪器时请严格遵循操作规程，使用完毕请清理实验台面并做好实验日志登记。</div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>

      <!-- 右侧：快捷入口与最近预约动态 -->
      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="card-header">
              <span class="header-title"><el-icon><Promotion /></el-icon> 快捷操作中心</span>
            </div>
          </template>
          <div class="quick-actions">
            <div class="quick-btn" @click="$router.push('/lab-list')">
              <div class="q-icon" style="background:#e6f7ff; color:#1890ff"><el-icon :size="24"><Calendar /></el-icon></div>
              <div class="q-text">新建预约</div>
            </div>
            <div class="quick-btn" @click="$router.push('/my-booking')">
              <div class="q-icon" style="background:#f6ffed; color:#52c41a"><el-icon :size="24"><Tickets /></el-icon></div>
              <div class="q-text">我的预约</div>
            </div>
            <div class="quick-btn" @click="$router.push('/ai-chat')">
              <div class="q-icon" style="background:#fff7e6; color:#fa8c16"><el-icon :size="24"><ChatDotRound /></el-icon></div>
              <div class="q-text">AI 问答</div>
            </div>
            <div class="quick-btn" @click="$router.push('/person')">
              <div class="q-icon" style="background:#f9f0ff; color:#722ed1"><el-icon :size="24"><User /></el-icon></div>
              <div class="q-text">个人资料</div>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span class="header-title"><el-icon><Clock /></el-icon> 实时预约动态</span>
            </div>
          </template>
          <el-timeline style="padding-left: 5px;">
            <el-timeline-item
              v-for="(item, index) in recentActivities"
              :key="index"
              :type="item.type"
              :timestamp="item.time"
              size="normal"
            >
              <span class="activity-text">{{ item.content }}</span>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboardStatsApi } from '@/api/booking'
import { getLabPageApi } from '@/api/lab'

const router = useRouter()
const stats = ref({
  lab_count: 8,
  device_count: 54,
  booking_count: 189,
  pending_count: 3
})

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch (e) {
    return {}
  }
})

const activeCollapse = ref(['1', '2'])
const hotLabs = ref([
  { id: 1, name: '人工智能与深度学习实验室 (A301)', location: '信息楼 3 楼', capacity: 45, status: 1 },
  { id: 2, name: '物联网与嵌入式系统实验室 (B204)', location: '工科实训楼 2 楼', capacity: 36, status: 1 },
  { id: 3, name: '计算机视觉与图形图像实验室 (C105)', location: '创新实验楼 1 楼', capacity: 30, status: 1 }
])

const recentActivities = ref([
  { content: '张同学预约了「人工智能实验室」下午时段', time: '10 分钟前', type: 'primary' },
  { content: '李老师审批通过了「物联网实验室」周五预约', time: '45 分钟前', type: 'success' },
  { content: '系统自动同步了 12 台新入库 GPU 工作站', time: '2 小时前', type: 'info' }
])

onMounted(async () => {
  try {
    const res = await getDashboardStatsApi().catch(() => null)
    if (res && res.data) {
      stats.value = res.data
    }
  } catch (e) {}

  try {
    const labRes = await getLabPageApi({ page: 1, size: 3 }).catch(() => null)
    if (labRes && labRes.data && labRes.data.list && labRes.data.list.length > 0) {
      hotLabs.value = labRes.data.list
    }
  } catch (e) {}
})

const handleGoLab = (id) => {
  router.push(`/lab-detail/${id}`)
}
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome-banner {
  background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
  border-radius: 12px;
  padding: 28px 32px;
  color: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.2);
  flex-wrap: wrap;
  gap: 20px;
}

.greeting {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}

.desc {
  font-size: 14px;
  opacity: 0.9;
}

.banner-right {
  display: flex;
  gap: 12px;
}

.stat-row {
  margin-top: 4px;
}

.stat-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 18px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  margin-bottom: 12px;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.stat-icon-wrapper {
  width: 54px;
  height: 54px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-blue .stat-icon-wrapper { background: #e6f7ff; color: #1890ff; }
.stat-green .stat-icon-wrapper { background: #f6ffed; color: #52c41a; }
.stat-orange .stat-icon-wrapper { background: #fff7e6; color: #fa8c16; }
.stat-purple .stat-icon-wrapper { background: #f9f0ff; color: #722ed1; }

.stat-title {
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #262626;
}

.unit {
  font-size: 12px;
  font-weight: normal;
  color: #8c8c8c;
}

.section-card {
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
  color: #262626;
  display: flex;
  align-items: center;
  gap: 6px;
}

.lab-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.hot-lab-item {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}

.hot-lab-item:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.lab-cover {
  height: 110px;
  background-color: #d9d9d9;
  background-size: cover;
  background-position: center;
  position: relative;
  padding: 8px;
}

.status-tag {
  position: absolute;
  right: 8px;
  top: 8px;
}

.lab-detail {
  padding: 12px;
}

.lab-name {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lab-meta, .lab-capacity {
  font-size: 12px;
  color: #8c8c8c;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-btn {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  border-color: #1890ff;
  background: #ffffff;
  transform: translateY(-2px);
}

.q-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.q-text {
  font-size: 13px;
  font-weight: 500;
  color: #262626;
}

.activity-text {
  font-size: 13px;
  color: #595959;
}
</style>
