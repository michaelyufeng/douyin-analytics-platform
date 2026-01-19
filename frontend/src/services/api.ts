import axios, { AxiosInstance } from 'axios'

// Create axios instance that returns data directly
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
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

// Response interceptor - extract data from response
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          break
        case 404:
          break
        case 500:
          break
      }
    }
    return Promise.reject(error)
  }
)

// Helper function for typed requests
const get = <T = any>(url: string, params?: object): Promise<T> =>
  api.get(url, { params }) as Promise<T>

const post = <T = any>(url: string, data?: object): Promise<T> =>
  api.post(url, data) as Promise<T>

const put = <T = any>(url: string, data?: object): Promise<T> =>
  api.put(url, data) as Promise<T>

const del = <T = any>(url: string): Promise<T> =>
  api.delete(url) as Promise<T>

// User API
export const userApi = {
  getProfile: (secUid: string) => get(`/users/profile/${secUid}`),
  getPosts: (secUid: string, cursor = 0, count = 20) =>
    get(`/users/posts/${secUid}`, { cursor, count }),
  getLikes: (secUid: string, cursor = 0, count = 20) =>
    get(`/users/likes/${secUid}`, { cursor, count }),
  getFollowing: (secUid: string, cursor = 0, count = 20) =>
    get(`/users/following/${secUid}`, { cursor, count }),
  getFollowers: (secUid: string, cursor = 0, count = 20) =>
    get(`/users/followers/${secUid}`, { cursor, count }),
  getHistory: (userId: number, days = 30) =>
    get(`/users/history/${userId}`, { days }),
  compare: (secUids: string[]) => post('/users/compare', { sec_uids: secUids }),
  batchGet: (secUids: string[]) => post('/users/batch', { sec_uids: secUids }),
}

// Video API
export const videoApi = {
  getDetail: (awemeId: string) => get(`/videos/detail/${awemeId}`),
  getComments: (awemeId: string, cursor = 0, count = 20) =>
    get(`/videos/comments/${awemeId}`, { cursor, count }),
  getReplies: (commentId: string, cursor = 0, count = 20) =>
    get(`/videos/replies/${commentId}`, { cursor, count }),
  getRelated: (awemeId: string, count = 20) =>
    get(`/videos/related/${awemeId}`, { count }),
  getHistory: (videoId: number, days = 30) =>
    get(`/videos/history/${videoId}`, { days }),
  parse: (url: string) => post('/videos/parse', { url }),
  download: (awemeId: string, quality = 'high') =>
    post('/videos/download', { aweme_id: awemeId, quality }),
}

// Live API
export const liveApi = {
  getInfo: (roomId: string) => get(`/lives/info/${roomId}`),
  getByUser: (secUid: string) => get(`/lives/by-user/${secUid}`),
  getDanmaku: (roomId: string, limit = 100) =>
    get(`/lives/danmaku/${roomId}`, { limit }),
  getRanking: (count = 50) => get('/lives/ranking', { count }),
  startRecord: (roomId: string) => post('/lives/record', { room_id: roomId }),
}

// Search API
export const searchApi = {
  searchVideo: (keyword: string, cursor = 0, count = 20, sortType = 0, publishTime = 0) =>
    get('/search/video', { keyword, cursor, count, sort_type: sortType, publish_time: publishTime }),
  searchUser: (keyword: string, cursor = 0, count = 20) =>
    get('/search/user', { keyword, cursor, count }),
  searchLive: (keyword: string, cursor = 0, count = 20) =>
    get('/search/live', { keyword, cursor, count }),
  getSuggest: (keyword: string) => get('/search/suggest', { keyword }),
  getTrending: () => get('/search/trending'),
}

// Ranking API
export const rankingApi = {
  getBoards: () => get('/ranking/boards'),
  getHotList: (boardType: string) => get(`/ranking/hot/${boardType}`),
  getVideoRanking: (count = 50) => get('/ranking/video', { count }),
  getLiveRanking: (count = 50) => get('/ranking/live', { count }),
}

// Task API
export const taskApi = {
  getTasks: (skip = 0, limit = 20, isActive?: boolean, taskType?: string) =>
    get('/tasks', { skip, limit, is_active: isActive, task_type: taskType }),
  createTask: (data: {
    task_type: string
    target_id: string
    target_name?: string
    interval_seconds?: number
  }) => post('/tasks', data),
  updateTask: (taskId: number, data: { target_name?: string; interval_seconds?: number; is_active?: boolean }) =>
    put(`/tasks/${taskId}`, data),
  deleteTask: (taskId: number) => del(`/tasks/${taskId}`),
  runTask: (taskId: number) => post(`/tasks/${taskId}/run`),
  getTaskLogs: (taskId: number, limit = 100) =>
    get(`/tasks/${taskId}/logs`, { limit }),
}

// Analysis API
export const analysisApi = {
  analyzeUser: (secUid: string) => post('/analysis/user', { sec_uid: secUid }),
  analyzeVideo: (awemeId: string) => post('/analysis/video', { aweme_id: awemeId }),
  analyzeComments: (awemeId: string) => post('/analysis/comments', { aweme_id: awemeId }),
  analyzeTrends: (keyword: string, days = 7) =>
    post('/analysis/trends', { keyword, days }),
  getReport: (reportId: number) => get(`/analysis/report/${reportId}`),
}

// Stats API
export const statsApi = {
  getStatistics: () => get('/stats'),
  getRecentActivities: (limit = 10) => get('/stats/recent', { limit }),
  getDataTrends: (days = 7) => get('/stats/trends', { days }),
}

// Auth API
export const authApi = {
  createQRCode: () => post<{
    success: boolean
    session_id?: string
    qr_image?: string
    message: string
    error?: string
  }>('/auth/qrcode/create'),
  checkQRStatus: (sessionId: string) => get<{
    status: string
    message: string
    cookie?: string
  }>(`/auth/qrcode/status/${sessionId}`),
  cancelQRLogin: (sessionId: string) => post(`/auth/qrcode/cancel/${sessionId}`),
  saveCookie: (cookie: string) => post<{
    success: boolean
    message: string
  }>('/auth/cookie/save', { cookie }),
  getCookieStatus: () => get<{
    has_cookie: boolean
    cookie_preview: string | null
    message: string
  }>('/auth/cookie/status'),
}

export default api
