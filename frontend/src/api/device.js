import request from '@/utils/request'

// 分页查询设备
export function getDevicePageApi(params) {
  return request({
    url: '/devices',
    method: 'get',
    params
  })
}

// 获取某实验室下的所有设备
export function getDevicesByLabIdApi(labId) {
  return request({
    url: `/devices/lab/${labId}`,
    method: 'get'
  })
}

// 新增设备
export function addDeviceApi(data) {
  return request({
    url: '/devices',
    method: 'post',
    data
  })
}

// 更新设备
export function updateDeviceApi(id, data) {
  return request({
    url: `/devices/${id}`,
    method: 'put',
    data
  })
}

// 删除设备
export function deleteDeviceApi(id) {
  return request({
    url: `/devices/${id}`,
    method: 'delete'
  })
}
