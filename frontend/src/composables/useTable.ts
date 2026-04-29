/**
 * 表格通用逻辑 Composable
 */
import { ref, reactive } from 'vue'

export interface TablePagination {
  page: number
  pageSize: number
  total: number
}

export interface UseTableOptions<T, F extends Record<string, any>> {
  fetchData: (params: any) => Promise<{ items: T[]; total: number }>
  initialFilters?: F
  pageSize?: number
}

export function useTable<T = any, F extends Record<string, any> = Record<string, any>>(options: UseTableOptions<T, F>) {
  const { fetchData, initialFilters = {} as F, pageSize = 20 } = options

  const loading = ref(false)
  const list = ref<T[]>([])
  const pagination = reactive<TablePagination>({
    page: 1,
    pageSize,
    total: 0
  })
  const filters = reactive<F>(initialFilters)

  const loadData = async () => {
    loading.value = true
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.pageSize,
        ...filters
      }
      const res = await fetchData(params)
      list.value = res.items || []
      pagination.total = res.total || 0
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  const handleSearch = () => {
    pagination.page = 1
    loadData()
  }

  const handleReset = () => {
    Object.assign(filters, initialFilters)
    handleSearch()
  }

  const handlePageChange = () => {
    loadData()
  }

  return {
    loading,
    list,
    pagination,
    filters,
    loadData,
    handleSearch,
    handleReset,
    handlePageChange
  }
}
