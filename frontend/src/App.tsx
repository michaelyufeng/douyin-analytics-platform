import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/Layout/MainLayout'
import Dashboard from './pages/Dashboard'
import UserAnalysis from './pages/UserAnalysis'
import VideoAnalysis from './pages/VideoAnalysis'
import CommentAnalysis from './pages/CommentAnalysis'
import LiveMonitor from './pages/LiveMonitor'
import HotRanking from './pages/HotRanking'
import TaskCenter from './pages/TaskCenter'
import DataAnalysis from './pages/DataAnalysis'
import Settings from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="user" element={<UserAnalysis />} />
          <Route path="video" element={<VideoAnalysis />} />
          <Route path="comment" element={<CommentAnalysis />} />
          <Route path="live" element={<LiveMonitor />} />
          <Route path="ranking" element={<HotRanking />} />
          <Route path="tasks" element={<TaskCenter />} />
          <Route path="analysis" element={<DataAnalysis />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
