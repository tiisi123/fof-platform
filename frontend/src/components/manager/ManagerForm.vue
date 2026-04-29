<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑管理人' : '新增管理人'"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="编号" prop="manager_code">
        <el-input
          v-model="formData.manager_code"
          placeholder="请输入管理人编号"
          :disabled="isEdit"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="名称" prop="manager_name">
        <el-input
          v-model="formData.manager_name"
          placeholder="请输入管理人名称"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="策略类型" prop="strategy_type">
        <el-select
          v-model="formData.strategy_type"
          placeholder="请选择策略类型"
          style="width: 100%"
        >
          <el-option
            v-for="item in STRATEGY_TYPES"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="评级" prop="rating">
        <el-select
          v-model="formData.rating"
          placeholder="请选择评级（可选）"
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="item in RATING_OPTIONS"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="formData.status">
          <el-radio label="active">活跃</el-radio>
          <el-radio label="inactive">停用</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          确定
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { Manager, ManagerCreate, ManagerUpdate } from '@/types'
import { STRATEGY_TYPES, RATING_OPTIONS } from '@/types/manager'

interface Props {
  visible: boolean
  manager?: Manager | null
  loading?: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'submit', data: ManagerCreate | ManagerUpdate): void
}

const props = withDefaults(defineProps<Props>(), {
  manager: null,
  loading: false
})

const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()

// 对话框可见性
const dialogVisible = ref(false)

// 是否为编辑模式
const isEdit = ref(false)

// 表单数据
const formData = reactive<ManagerCreate>({
  manager_code: '',
  manager_name: '',
  strategy_type: '',
  rating: undefined,
  status: 'active'
})

// 表单验证规则
const rules: FormRules = {
  manager_code: [
    { required: true, message: '请输入管理人编号', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  manager_name: [
    { required: true, message: '请输入管理人名称', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  strategy_type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 监听visible变化
watch(() => props.visible, (val) => {
  dialogVisible.value = val
  if (val) {
    // 打开对话框时初始化表单
    isEdit.value = !!props.manager
    if (props.manager) {
      // 编辑模式，填充数据
      Object.assign(formData, {
        manager_code: props.manager.manager_code,
        manager_name: props.manager.manager_name,
        strategy_type: props.manager.strategy_type,
        rating: props.manager.rating || undefined,
        status: props.manager.status
      })
    } else {
      // 新增模式，重置表单
      resetForm()
    }
  }
})

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    manager_code: '',
    manager_name: '',
    strategy_type: '',
    rating: undefined,
    status: 'active'
  })
  formRef.value?.clearValidate()
}

// 处理关闭
const handleClose = () => {
  emit('update:visible', false)
  resetForm()
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    // 准备提交数据
    const submitData: ManagerCreate | ManagerUpdate = isEdit.value
      ? {
          manager_name: formData.manager_name,
          strategy_type: formData.strategy_type,
          rating: formData.rating || undefined,
          status: formData.status
        }
      : {
          manager_code: formData.manager_code,
          manager_name: formData.manager_name,
          strategy_type: formData.strategy_type,
          rating: formData.rating || undefined,
          status: formData.status
        }

    emit('submit', submitData)
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
