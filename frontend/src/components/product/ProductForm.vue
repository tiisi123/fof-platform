<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑产品' : '新增产品'"
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
      <el-form-item label="产品代码" prop="product_code">
        <el-input
          v-model="formData.product_code"
          placeholder="请输入产品代码"
          :disabled="isEdit"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="产品名称" prop="product_name">
        <el-input
          v-model="formData.product_name"
          placeholder="请输入产品名称"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="管理人" prop="manager_id">
        <el-select
          v-model="formData.manager_id"
          placeholder="请选择管理人"
          filterable
          style="width: 100%"
          :loading="managersLoading"
        >
          <el-option
            v-for="manager in managers"
            :key="manager.id"
            :label="manager.manager_name"
            :value="manager.id"
          />
        </el-select>
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

      <el-form-item label="状态" prop="status">
        <el-select
          v-model="formData.status"
          placeholder="请选择状态"
          style="width: 100%"
        >
          <el-option
            v-for="item in PRODUCT_STATUS_OPTIONS"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="成立日期" prop="established_date">
        <el-date-picker
          v-model="formData.established_date"
          type="date"
          placeholder="请选择成立日期"
          style="width: 100%"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="清算日期" prop="liquidation_date">
        <el-date-picker
          v-model="formData.liquidation_date"
          type="date"
          placeholder="请选择清算日期（可选）"
          style="width: 100%"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          clearable
        />
      </el-form-item>

      <el-form-item label="管理费率" prop="management_fee">
        <el-input-number
          v-model="formData.management_fee"
          :precision="2"
          :min="0"
          :max="100"
          placeholder="如 1.50"
          style="width: 100%"
          controls-position="right"
        />
        <span style="margin-left: 8px; color: var(--text-secondary)">%</span>
      </el-form-item>

      <el-form-item label="业绩报酬" prop="performance_fee">
        <el-input-number
          v-model="formData.performance_fee"
          :precision="2"
          :min="0"
          :max="100"
          placeholder="如 20.00"
          style="width: 100%"
          controls-position="right"
        />
        <span style="margin-left: 8px; color: var(--text-secondary)">%</span>
      </el-form-item>

      <el-form-item label="基准代码" prop="benchmark_code">
        <el-input
          v-model="formData.benchmark_code"
          placeholder="如 000300.SH"
          maxlength="50"
        />
      </el-form-item>

      <el-form-item label="基准名称" prop="benchmark_name">
        <el-input
          v-model="formData.benchmark_name"
          placeholder="如 沪深300"
          maxlength="100"
        />
      </el-form-item>

      <el-form-item label="是否在投" prop="is_invested">
        <el-switch v-model="formData.is_invested" />
      </el-form-item>

      <el-form-item label="备注" prop="remark">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入备注"
          maxlength="1000"
          show-word-limit
        />
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
import { ref, reactive, watch, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { Product, ProductCreate, ProductUpdate } from '@/types'
import { PRODUCT_STATUS_OPTIONS } from '@/types/product'
import { STRATEGY_TYPES } from '@/types/manager'
import { managerApi } from '@/api/manager'
import type { Manager } from '@/types'

interface Props {
  visible: boolean
  product?: Product | null
  loading?: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'submit', data: ProductCreate | ProductUpdate): void
}

const props = withDefaults(defineProps<Props>(), {
  product: null,
  loading: false
})

const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()

// 对话框可见性
const dialogVisible = ref(false)

// 是否为编辑模式
const isEdit = ref(false)

// 管理人列表
const managers = ref<Manager[]>([])
const managersLoading = ref(false)

// 表单数据
const formData = reactive<ProductCreate>({
  product_code: '',
  product_name: '',
  manager_id: 0,
  strategy_type: '',
  status: 'active',
  established_date: undefined,
  liquidation_date: undefined,
  management_fee: undefined,
  performance_fee: undefined,
  benchmark_code: undefined,
  benchmark_name: undefined,
  is_invested: false,
  remark: undefined
})

// 表单验证规则
const rules: FormRules = {
  product_code: [
    { required: true, message: '请输入产品代码', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  product_name: [
    { required: true, message: '请输入产品名称', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  manager_id: [
    { required: true, message: '请选择管理人', trigger: 'change' }
  ],
  strategy_type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 获取管理人列表
const fetchManagers = async () => {
  managersLoading.value = true
  try {
    const response = await managerApi.getList({ skip: 0, limit: 1000, status: 'active' })
    managers.value = response.items
  } catch (error) {
    console.error('获取管理人列表失败:', error)
  } finally {
    managersLoading.value = false
  }
}

// 监听visible变化
watch(() => props.visible, (val) => {
  dialogVisible.value = val
  if (val) {
    // 打开对话框时初始化表单
    isEdit.value = !!props.product
    if (props.product) {
      // 编辑模式，填充数据
      Object.assign(formData, {
        product_code: props.product.product_code,
        product_name: props.product.product_name,
        manager_id: props.product.manager_id,
        strategy_type: props.product.strategy_type,
        status: props.product.status,
        established_date: props.product.established_date || undefined,
        liquidation_date: props.product.liquidation_date || undefined,
        management_fee: props.product.management_fee,
        performance_fee: props.product.performance_fee,
        benchmark_code: props.product.benchmark_code,
        benchmark_name: props.product.benchmark_name,
        is_invested: props.product.is_invested || false,
        remark: props.product.remark
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
    product_code: '',
    product_name: '',
    manager_id: 0,
    strategy_type: '',
    status: 'active',
    established_date: undefined,
    liquidation_date: undefined,
    management_fee: undefined,
    performance_fee: undefined,
    benchmark_code: undefined,
    benchmark_name: undefined,
    is_invested: false,
    remark: undefined
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
    const submitData: ProductCreate | ProductUpdate = isEdit.value
      ? {
          product_name: formData.product_name,
          manager_id: formData.manager_id,
          strategy_type: formData.strategy_type,
          status: formData.status,
          established_date: formData.established_date || undefined,
          liquidation_date: formData.liquidation_date || undefined,
          management_fee: formData.management_fee,
          performance_fee: formData.performance_fee,
          benchmark_code: formData.benchmark_code,
          benchmark_name: formData.benchmark_name,
          is_invested: formData.is_invested,
          remark: formData.remark
        }
      : {
          product_code: formData.product_code,
          product_name: formData.product_name,
          manager_id: formData.manager_id,
          strategy_type: formData.strategy_type,
          status: formData.status,
          established_date: formData.established_date || undefined,
          liquidation_date: formData.liquidation_date || undefined,
          management_fee: formData.management_fee,
          performance_fee: formData.performance_fee,
          benchmark_code: formData.benchmark_code,
          benchmark_name: formData.benchmark_name,
          is_invested: formData.is_invested,
          remark: formData.remark
        }

    emit('submit', submitData)
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 初始化
onMounted(() => {
  fetchManagers()
})
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
