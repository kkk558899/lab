<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1 class="code">404</h1>
      <p class="desc">抱歉，您访问的页面不存在或已被移除</p>
      <el-button type="primary" round @click="$router.push('/home')">返回系统首页</el-button>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
}

.not-found-content {
  text-align: center;
}

.code {
  font-size: 80px;
  color: #409eff;
  margin-bottom: 12px;
  font-weight: 800;
}

.desc {
  font-size: 16px;
  color: #8c8c8c;
  margin-bottom: 24px;
}
</style>
