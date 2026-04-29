import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Product, ProductCreate, ProductUpdate, ProductListParams } from '@/types'
import { productApi } from '@/api/product'
import { ElMessage } from 'element-plus'

/**
 * 产品Store
 * 管理产品数据和操作
 */
export const useProductStore = defineStore('product', () => {
  // 状态
  const products = ref<Product[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentProduct = ref<Product | null>(null)

  /**
   * 获取产品列表
   */
  const fetchProducts = async (params?: ProductListParams) => {
    loading.value = true
    try {
      const response = await productApi.getList(params)
      products.value = response.items
      total.value = response.total
      return response
    } catch (error) {
      console.error('获取产品列表失败:', error)
      ElMessage.error('获取产品列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取产品详情
   */
  const fetchProductById = async (id: number) => {
    loading.value = true
    try {
      const product = await productApi.getById(id)
      currentProduct.value = product
      return product
    } catch (error) {
      console.error('获取产品详情失败:', error)
      ElMessage.error('获取产品详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建产品
   */
  const createProduct = async (data: ProductCreate) => {
    loading.value = true
    try {
      const product = await productApi.create(data)
      ElMessage.success('创建产品成功')
      return product
    } catch (error) {
      console.error('创建产品失败:', error)
      ElMessage.error('创建产品失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新产品
   */
  const updateProduct = async (id: number, data: ProductUpdate) => {
    loading.value = true
    try {
      const product = await productApi.update(id, data)
      ElMessage.success('更新产品成功')
      return product
    } catch (error) {
      console.error('更新产品失败:', error)
      ElMessage.error('更新产品失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除产品
   */
  const deleteProduct = async (id: number) => {
    loading.value = true
    try {
      await productApi.delete(id)
      ElMessage.success('删除产品成功')
    } catch (error) {
      console.error('删除产品失败:', error)
      ElMessage.error('删除产品失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 重置状态
   */
  const reset = () => {
    products.value = []
    total.value = 0
    loading.value = false
    currentProduct.value = null
  }

  return {
    // 状态
    products,
    total,
    loading,
    currentProduct,

    // 方法
    fetchProducts,
    fetchProductById,
    createProduct,
    updateProduct,
    deleteProduct,
    reset
  }
})
