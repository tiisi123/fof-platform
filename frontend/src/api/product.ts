/**
 * 产品API
 */
import request from './request'
import type {
  Product,
  ProductCreate,
  ProductUpdate,
  ProductListParams,
  ProductListResponse,
  ProductStatistics
} from '@/types'

// 添加兼容别名
const addProductAliases = (product: Product): Product => {
  return {
    ...product,
    code: product.product_code,
    name: product.product_name
  }
}

export const productApi = {
  /**
   * 获取产品列表
   */
  async getList(params?: ProductListParams): Promise<ProductListResponse> {
    const response = await request({
      url: '/products',
      method: 'get',
      params
    }) as ProductListResponse
    response.items = response.items.map(addProductAliases)
    return response
  },

  /**
   * 获取产品详情
   */
  async getById(id: number): Promise<Product> {
    const product = await request({
      url: `/products/${id}`,
      method: 'get'
    }) as Product
    return addProductAliases(product)
  },

  /**
   * 创建产品
   */
  create(data: ProductCreate): Promise<Product> {
    return request({
      url: '/products',
      method: 'post',
      data
    })
  },

  /**
   * 更新产品
   */
  update(id: number, data: ProductUpdate): Promise<Product> {
    return request({
      url: `/products/${id}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除产品
   */
  delete(id: number): Promise<{ message: string }> {
    return request({
      url: `/products/${id}`,
      method: 'delete'
    })
  },

  /**
   * 获取产品统计信息
   */
  getStatistics(): Promise<ProductStatistics> {
    return request({
      url: '/products/statistics/summary',
      method: 'get'
    })
  }
}
