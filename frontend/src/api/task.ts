/**
 * 待办任务API
 */
import request from './request'

export interface TaskListParams {
  status?: string
  priority?: string
  assigned_to?: number
  my_tasks?: boolean
  keyword?: string
  page?: number
  page_size?: number
}

export interface TaskCreate {
  title: string
  description?: string
  priority?: string
  due_date?: string
  assigned_to?: number
  product_id?: number
  manager_id?: number
  portfolio_id?: number
}

export interface TaskItem {
  id: number
  title: string
  description: string | null
  status: string
  priority: string
  product_id: number | null
  manager_id: number | null
  portfolio_id: number | null
  product_name: string | null
  manager_name: string | null
  portfolio_name: string | null
  assigned_to: number | null
  assignee_name: string | null
  created_by: number
  creator_name: string | null
  due_date: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface TaskStats {
  total: number
  pending: number
  in_progress: number
  completed: number
  my_pending: number
  overdue: number
}

export const taskApi = {
  getList(params?: TaskListParams): Promise<{ total: number; items: TaskItem[] }> {
    return request({ url: '/tasks', method: 'get', params })
  },

  getById(id: number): Promise<TaskItem> {
    return request({ url: `/tasks/${id}`, method: 'get' })
  },

  create(data: TaskCreate): Promise<{ id: number; message: string }> {
    return request({ url: '/tasks', method: 'post', data })
  },

  update(id: number, data: Partial<TaskCreate & { status: string }>): Promise<{ message: string }> {
    return request({ url: `/tasks/${id}`, method: 'put', data })
  },

  complete(id: number): Promise<{ message: string }> {
    return request({ url: `/tasks/${id}/complete`, method: 'put' })
  },

  delete(id: number): Promise<{ message: string }> {
    return request({ url: `/tasks/${id}`, method: 'delete' })
  },

  getStats(): Promise<TaskStats> {
    return request({ url: '/tasks/stats', method: 'get' })
  },
}
