import request from '@/utils/request'

// 用户登录
export function loginApi(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

// 用户注册
export function registerApi(data) {
  return request({
    url: '/auth/register',
    method: 'post',
    data
  })
}

// 获取当前登录用户信息
export function getMeApi() {
  return request({
    url: '/auth/me',
    method: 'get'
  })
}
