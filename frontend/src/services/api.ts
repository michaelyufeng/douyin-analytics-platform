import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      // Handle specific error codes
      switch (error.response.status) {
        case 401:
          // Unauthorized
          break
        case 404:
          // Not found
          break
        case 500:
          // Server error
          break
      }
    }
    return Promise.reject(error)
  }
)

// User API
export const userApi = {
  getProfile: (secUid: string) => api.get(`/users/profile/${secUid}`),
  getPosts: (secUid: string, cursor = 0, count = 20) =>
    api.get(`/users/posts/${secUid}`, { params: { cursor, count } }),
  getLikes: (secUid: string, cursor = 0, count = 20) =>
    api.get(`/users/likes/${secUid}`, { params: { cursor, count } }),
  getFollowing: (secUid: string, cursor = 0, count = 20) =>
    api.get(`/users/following/${secUid}`, { params: { cursor, count } }),
  getFollowers: (secUid: string, cursor = 0, count = 20) =>
    api.get(`/users/followers/${secUid}`, { params: { cursor, count } }),
  getHistory: (userId: number, days = 30) =>
    api.get(`/users/history/${userId}`, { params: { days } }),
  compare: (secUids: string[]) => api.post('/users/compare', { sec_uids: secUids }),
  batchGet: (secUids: string[]) => api.post('/users/batch', { sec_uids: secUids }),
}

// Video API
export const videoApi = {
  getDetail: (awemeId: string) => api.get(`/videos/detail/${awemeId}`),
  getComments: (awemeId: string, cursor = 0, count = 20) =>
    api.get(`/videos/comments/${awemeId}`, { params: { cursor, count } }),
  getReplies: (commentId: string, cursor = 0, count = 20) =>
    api.get(`/videos/replies/${commentId}`, { params: { cursor, count } }),
  getRelated: (awemeId: string, count = 20) =>
    api.get(`/videos/related/${awemeId}`, { params: { count } }),
  getHistory: (videoId: number, days = 30) =>
    api.get(`/videos/history/${videoId}`, { params: { days } }),
  parse: (url: string) => api.post('/videos/parse', { url }),
  download: (awemeId: string, quality = 'high') =>
    api.post('/videos/download', { aweme_id: awemeId, quality }),
}

// Live API
export const liveApi = {
  getInfo: (roomId: string) => api.get(`/lives/info/${roomId}`),
  getByUser: (secUid: string) => api.get(`/lives/by-user/${secUid}`),
  getDanmaku: (roomId: string, limit = 100) =>
    api.get(`/lives/danmaku/${roomId}`, { params: { limit } }),
  getRanking: (count = 50) => api.get('/lives/ranking', { params: { count } }),
  startRecord: (roomId: string) => api.post('/lives/record', { room_id: roomId }),
}

// Search API
export const searchApi = {
  searchVideo: (keyword: string, cursor = 0, count = 20, sortType = 0, publishTime = 0) =>
    api.get('/search/video', {
      params: { keyword, cursor, count, sort_type: sortType, publish_time: publishTime },
    }),
  searchUser: (keyword: string, cursor = 0, count = 20) =>
    api.get('/search/user', { params: { keyword, cursor, count } }),
  searchLive: (keyword: string, cursor = 0, count = 20) =>
    api.get('/search/live', { params: { keyword, cursor, count } }),
  getSuggest: (keyword: string) => api.get('/search/suggest', { params: { keyword } }),
  getTrending: () => api.get('/search/trending'),
}

// Ranking API
export const rankingApi = {
  getBoards: () => api.get('/ranking/boards'),
  getHotList: (boardType: string) => api.get(`/ranking/hot/${boardType}`),
  getVideoRanking: (count = 50) => api.get('/ranking/video', { params: { count } }),
  getLiveRanking: (count = 50) => api.get('/ranking/live', { params: { count } }),
}

// Task API
export const taskApi = {
  getTasks: (skip = 0, limit = 20, isActive?: boolean, taskType?: string) =>
    api.get('/tasks', { params: { skip, limit, is_active: isActive, task_type: taskType } }),
  createTask: (data: {
    task_type: string
    target_id: string
    target_name?: string
    interval_seconds?: number
  }) => api.post('/tasks', data),
  updateTask: (taskId: number, data: { target_name?: string; interval_seconds?: number; is_active?: boolean }) =>
    api.put(`/tasks/${taskId}`, data),
  deleteTask: (taskId: number) => api.delete(`/tasks/${taskId}`),
  runTask: (taskId: number) => api.post(`/tasks/${taskId}/run`),
  getTaskLogs: (taskId: number, limit = 100) =>
    api.get(`/tasks/${taskId}/logs`, { params: { limit } }),
}

// Analysis API
export const analysisApi = {
  analyzeUser: (secUid: string) => api.post('/analysis/user', { sec_uid: secUid }),
  analyzeVideo: (awemeId: string) => api.post('/analysis/video', { aweme_id: awemeId }),
  analyzeComments: (awemeId: string) => api.post('/analysis/comments', { aweme_id: awemeId }),
  analyzeTrends: (keyword: string, days = 7) =>
    api.post('/analysis/trends', { keyword, days }),
  getReport: (reportId: number) => api.get(`/analysis/report/${reportId}`),
}

// Stats API
export const statsApi = {
  getStatistics: () => api.get('/stats'),
  getRecentActivities: (limit = 10) => api.get('/stats/recent', { params: { limit } }),
  getDataTrends: (days = 7) => api.get('/stats/trends', { params: { days } }),
}

export default api
