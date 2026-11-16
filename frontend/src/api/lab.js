import request from '@/utils/request'

// 分页查询实验室
export function getLabPageApi(params) {
  return request({
    url: '/labs',
    method: 'get',
    params
  })
}

// 获取所有实验室列表(不分页)
export function getLabListApi() {
  return request({
    url: '/labs/all',
    method: 'get'
  })
}

// 获取实验室详情
export function getLabByIdApi(id) {
  return request({
    url: `/labs/${id}`,
    method: 'get'
  })
}

// 新增实验室
export function addLabApi(data) {
  return request({
    url: '/labs',
    method: 'post',
    data
  })
}

// 更新实验室
export function updateLabApi(id, data) {
  return request({
    url: `/labs/${id}`,
    method: 'put',
    data
  })
}

// 删除实验室
export function deleteLabApi(id) {
  return request({
    url: `/labs/${id}`,
    method: 'delete'
  })
}

// 批量删除实验室
export function batchDeleteLabApi(ids) {
  return request({
    url: '/labs/batch',
    method: 'delete',
    data: { ids }
  })
}
