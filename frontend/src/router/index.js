import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/layout/Layout.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        meta: { title: '系统首页' },
        component: () => import('@/views/Home.vue')
      },
      {
        path: 'lab-list',
        name: 'LabList',
        meta: { title: '实验室大厅' },
        component: () => import('@/views/LabList.vue')
      },
      {
        path: 'lab-detail/:id',
        name: 'LabDetail',
        meta: { title: '实验室详情' },
        component: () => import('@/views/LabDetail.vue')
      },
      {
        path: 'ai-chat',
        name: 'AiChat',
        meta: { title: '智能AI助手' },
        component: () => import('@/views/AiChat.vue')
      },
      {
        path: 'my-booking',
        name: 'MyBooking',
        meta: { title: '我的预约' },
        component: () => import('@/views/MyBooking.vue')
      },
      {
        path: 'booking-manage',
        name: 'BookingManage',
        meta: { title: '预约审核管理', requireAdmin: true },
        component: () => import('@/views/BookingManage.vue')
      },
      {
        path: 'lab',
        name: 'Lab',
        meta: { title: '实验室管理', requireAdmin: true },
        component: () => import('@/views/Lab.vue')
      },
      {
        path: 'device',
        name: 'Device',
        meta: { title: '设备管理', requireAdmin: true },
        component: () => import('@/views/Device.vue')
      },
      {
        path: 'user',
        name: 'User',
        meta: { title: '用户权限管理', requireAdmin: true },
        component: () => import('@/views/User.vue')
      },
      {
        path: 'person',
        name: 'Person',
        meta: { title: '个人信息' },
        component: () => import('@/views/Person.vue')
      },
      {
        path: 'password',
        name: 'Password',
        meta: { title: '修改密码' },
        component: () => import('@/views/Password.vue')
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    meta: { title: '用户登录' },
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    meta: { title: '用户注册' },
    component: () => import('@/views/Register.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    meta: { title: '404 页面未找到' },
    component: () => import('@/views/404.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智能实验室预约系统`
  }

  const token = localStorage.getItem('token')
  const whiteList = ['/login', '/register']

  if (whiteList.includes(to.path)) {
    if (token && to.path === '/login') {
      next('/home')
    } else {
      next()
    }
  } else {
    if (token) {
      next()
    } else {
      next('/login')
    }
  }
})

export default router
