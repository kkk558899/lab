import request from '@/utils/request'

// 创建预约申请 (学生/老师)
export function createBookingApi(data) {
  return request({
    url: '/bookings',
    method: 'post',
    data
  })
}

// 查询我的预约记录
export function getMyBookingsApi(params) {
  return request({
    url: '/bookings/my',
    method: 'get',
    params
  })
}

// 管理员分页查询所有预约
export function getBookingPageApi(params) {
  return request({
    url: '/bookings',
    method: 'get',
    params
  })
}

// 审核预约 (通过/拒绝)
export function auditBookingApi(id, data) {
  return request({
    url: `/bookings/${id}/audit`,
    method: 'put',
    data
  })
}

// 取消预约
export function cancelBookingApi(id) {
  return request({
    url: `/bookings/${id}/cancel`,
    method: 'put'
  })
}

// 获取系统仪表盘统计数据
export function getDashboardStatsApi() {
  return request({
    url: '/dashboard/stats',
    method: 'get'
  })
}
