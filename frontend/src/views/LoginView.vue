<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = ref({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 已登录则直接跳转
if (authStore.isLoggedIn) {
  router.replace('/admin/dashboard')
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  loading.value = true
  try {
    await authStore.login(form.value)
    ElMessage.success('登录成功')
    router.push('/admin/dashboard')
  } catch {
    ElMessage.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    style="
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background: #f0f2f5;
    "
  >
    <el-card style="width: 400px" shadow="always">
      <template #header>
        <h2 style="text-align: center; margin: 0">🔐 管理后台登录</h2>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div style="text-align: center; color: #909399; font-size: 12px">仅管理员可访问</div>
    </el-card>
  </div>
</template>
