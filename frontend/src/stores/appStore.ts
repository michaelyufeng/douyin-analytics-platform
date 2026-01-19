import { create } from 'zustand'

interface UserProfile {
  id: number
  sec_uid: string
  nickname: string
  unique_id: string
  avatar_url: string
  follower_count: number
  following_count: number
  total_favorited: number
  aweme_count: number
  is_verified: boolean
  signature: string
}

interface Video {
  id?: number
  aweme_id: string
  desc: string
  video_url: string
  cover_url: string
  play_count: number
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  create_time: string
}

interface Task {
  id: number
  task_type: string
  target_id: string
  target_name: string
  interval_seconds: number
  is_active: boolean
  last_run: string | null
  next_run: string | null
  created_at: string
}

interface AppState {
  // User state
  currentUser: UserProfile | null
  setCurrentUser: (user: UserProfile | null) => void

  // Video state
  currentVideo: Video | null
  setCurrentVideo: (video: Video | null) => void

  // Tasks state
  tasks: Task[]
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  removeTask: (taskId: number) => void
  updateTask: (taskId: number, data: Partial<Task>) => void

  // UI state
  loading: boolean
  setLoading: (loading: boolean) => void

  // Search state
  searchKeyword: string
  setSearchKeyword: (keyword: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  // User state
  currentUser: null,
  setCurrentUser: (user) => set({ currentUser: user }),

  // Video state
  currentVideo: null,
  setCurrentVideo: (video) => set({ currentVideo: video }),

  // Tasks state
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
  removeTask: (taskId) =>
    set((state) => ({ tasks: state.tasks.filter((t) => t.id !== taskId) })),
  updateTask: (taskId, data) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === taskId ? { ...t, ...data } : t)),
    })),

  // UI state
  loading: false,
  setLoading: (loading) => set({ loading }),

  // Search state
  searchKeyword: '',
  setSearchKeyword: (keyword) => set({ searchKeyword: keyword }),
}))
