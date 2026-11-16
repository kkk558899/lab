import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const res = response.data
    // 如果返回的是二进制文件流 (如导出或图片)
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return res
    }

    // 成功响应 (支持 code 为 200 或 0)
    if (res.code === 200 || res.code === 0 || res.code === '200') {
      return res
    }

    // 401: Token 失效或未登录
    if (res.code === 401 || res.code === '401') {
      ElMessage.error(res.message || res.msg || '登录状态已失效，请重新登录')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
      return Promise.reject(new Error(res.message || res.msg || 'Error'))
    }

    // 业务错误
    ElMessage.error(res.message || res.msg || '请求处理失败')
    return Promise.reject(new Error(res.message || res.msg || 'Error'))
  },
  error => {
    console.error('响应异常:', error)
    if (error.response) {
      if (error.response.status === 401) {
        ElMessage.error('登录状态已失效，请重新登录')
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
      } else {
        const errorMsg = error.response.data?.message || error.response.data?.msg || error.response.data?.detail || '网络异常，请稍后重试'
        ElMessage.error(errorMsg)
      }
    } else {
      ElMessage.error(error.message || '网络连接失败')
    }
    return Promise.reject(error)
  }
)

export default request
