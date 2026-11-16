import request from '@/utils/request'

// 分页查询用户列表
export function getUserPageApi(params) {
  return request({
    url: '/users',
    method: 'get',
    params
  })
}

// 新增用户
export function addUserApi(data) {
  return request({
    url: '/users',
    method: 'post',
    data
  })
}

// 修改用户
export function updateUserApi(id, data) {
  return request({
    url: `/users/${id}`,
    method: 'put',
    data
  })
}

// 删除单个用户
export function deleteUserApi(id) {
  return request({
    url: `/users/${id}`,
    method: 'delete'
  })
}

// 批量删除用户
export function batchDeleteUserApi(ids) {
  return request({
    url: '/users/batch',
    method: 'delete',
    data: { ids }
  })
}

// 修改个人资料
export function updateProfileApi(data) {
  return request({
    url: '/users/profile',
    method: 'put',
    data
  })
}

// 修改密码
export function updatePasswordApi(data) {
  return request({
    url: '/users/password',
    method: 'put',
    data
  })
}
