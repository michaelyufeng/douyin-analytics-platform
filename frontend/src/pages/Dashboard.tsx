import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, List, Tag, Input, Button, message, Spin, Empty } from 'antd'
import {
  UserOutlined,
  PlayCircleOutlined,
  FireOutlined,
  ScheduleOutlined,
  SearchOutlined,
  VideoCameraOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { rankingApi, searchApi, statsApi } from '../services/api'
import { formatNumber, formatTimeAgo } from '../utils/format'

interface HotItem {
  word: string
  hot_value: number
  position: number
}

interface Activity {
  type: string
  text: string
  time: string | null
  icon: string
}

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  color: string
  suffix?: string
  loading?: boolean
}

const StatCard = ({ title, value, icon, color, suffix, loading }: StatCardProps) => (
  <Card className="hover-card" bordered={false}>
    <Spin spinning={loading}>
      <Row align="middle" gutter={16}>
        <Col>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              background: color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 24,
              color: '#fff',
            }}
          >
            {icon}
          </div>
        </Col>
        <Col flex={1}>
          <Statistic
            title={title}
            value={value}
            suffix={suffix}
            valueStyle={{ fontSize: 24, fontWeight: 600 }}
          />
        </Col>
      </Row>
    </Spin>
  </Card>
)

const getActivityIcon = (iconType: string) => {
  switch (iconType) {
    case 'user':
      return <UserOutlined style={{ color: '#1890ff' }} />
    case 'video':
      return <VideoCameraOutlined style={{ color: '#52c41a' }} />
    case 'task':
      return <ScheduleOutlined style={{ color: '#faad14' }} />
    default:
      return <MessageOutlined style={{ color: '#999' }} />
  }
}

const Dashboard = () => {
  const navigate = useNavigate()
  const [searchValue, setSearchValue] = useState('')
  const [hotList, setHotList] = useState<HotItem[]>([])
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(false)
  const [statsLoading, setStatsLoading] = useState(false)
  const [activitiesLoading, setActivitiesLoading] = useState(false)
  const [stats, setStats] = useState({
    users: 0,
    videos: 0,
    tasks: 0,
    comments: 0,
  })

  useEffect(() => {
    fetchStats()
    fetchHotList()
    fetchActivities()
  }, [])

  const fetchStats = async () => {
    setStatsLoading(true)
    try {
      const data = await statsApi.getStatistics()
      if (data) {
        setStats({
          users: data.users || 0,
          videos: data.videos || 0,
          tasks: data.tasks || 0,
          comments: data.comments || 0,
        })
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setStatsLoading(false)
    }
  }

  const fetchHotList = async () => {
    setLoading(true)
    try {
      const data = await searchApi.getTrending()
      if (data?.trends) {
        setHotList(data.trends.slice(0, 20))
      }
    } catch (error) {
      console.error('Failed to fetch hot list:', error)
      setHotList([])
    } finally {
      setLoading(false)
    }
  }

  const fetchActivities = async () => {
    setActivitiesLoading(true)
    try {
      const data = await statsApi.getRecentActivities(10)
      if (data?.activities) {
        setActivities(data.activities)
      }
    } catch (error) {
      console.error('Failed to fetch activities:', error)
      setActivities([])
    } finally {
      setActivitiesLoading(false)
    }
  }

  const handleSearch = () => {
    if (!searchValue.trim()) {
      message.warning('请输入搜索内容')
      return
    }

    // Detect URL type and navigate accordingly
    if (searchValue.includes('douyin.com')) {
      if (searchValue.includes('/video/')) {
        navigate('/video', { state: { url: searchValue } })
      } else if (searchValue.includes('/user/')) {
        navigate('/user', { state: { url: searchValue } })
      } else if (searchValue.includes('live.douyin.com')) {
        navigate('/live', { state: { url: searchValue } })
      }
    } else {
      // Treat as keyword search
      navigate('/video', { state: { keyword: searchValue } })
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据概览</h2>

      {/* Quick Search */}
      <Card bordered={false} style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col flex={1}>
            <Input
              size="large"
              placeholder="输入抖音链接或关键词快速分析..."
              prefix={<SearchOutlined />}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onPressEnter={handleSearch}
            />
          </Col>
          <Col>
            <Button type="primary" size="large" icon={<SearchOutlined />} onClick={handleSearch}>
              开始分析
            </Button>
          </Col>
        </Row>
        <div style={{ marginTop: 12, color: '#999', fontSize: 12 }}>
          支持抖音用户主页、视频链接、直播链接，或直接输入关键词搜索
        </div>
      </Card>

      {/* Stats Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="已采集用户"
            value={stats.users}
            icon={<UserOutlined />}
            color="#1890ff"
            loading={statsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="已采集视频"
            value={stats.videos}
            icon={<PlayCircleOutlined />}
            color="#52c41a"
            loading={statsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="监控任务"
            value={stats.tasks}
            icon={<ScheduleOutlined />}
            color="#faad14"
            loading={statsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="已采集评论"
            value={stats.comments}
            icon={<MessageOutlined />}
            color="#f5222d"
            loading={statsLoading}
          />
        </Col>
      </Row>

      {/* Hot List and Quick Actions */}
      <Row gutter={16}>
        <Col xs={24} lg={16}>
          <Card
            title={
              <span>
                <FireOutlined style={{ color: '#f5222d', marginRight: 8 }} />
                实时热榜
              </span>
            }
            bordered={false}
            extra={
              <Button type="link" onClick={() => navigate('/ranking')}>
                查看全部
              </Button>
            }
          >
            <Spin spinning={loading}>
              {hotList.length > 0 ? (
                <List
                  dataSource={hotList}
                  renderItem={(item, index) => (
                    <List.Item
                      actions={[
                        <span key="hot" style={{ color: '#999' }}>
                          {formatNumber(item.hot_value)} 热度
                        </span>,
                      ]}
                    >
                      <List.Item.Meta
                        avatar={
                          <Tag
                            color={index < 3 ? '#f5222d' : index < 6 ? '#fa8c16' : 'default'}
                            style={{ width: 24, textAlign: 'center' }}
                          >
                            {index + 1}
                          </Tag>
                        }
                        title={
                          <a
                            onClick={() => navigate('/video', { state: { keyword: item.word } })}
                            style={{ color: 'inherit' }}
                          >
                            {item.word}
                          </a>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无热榜数据，请配置抖音Cookie后使用" />
              )}
            </Spin>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="快捷操作" bordered={false} style={{ marginBottom: 16 }}>
            <Row gutter={[12, 12]}>
              <Col span={12}>
                <Button
                  block
                  icon={<UserOutlined />}
                  onClick={() => navigate('/user')}
                >
                  用户分析
                </Button>
              </Col>
              <Col span={12}>
                <Button
                  block
                  icon={<PlayCircleOutlined />}
                  onClick={() => navigate('/video')}
                >
                  视频分析
                </Button>
              </Col>
              <Col span={12}>
                <Button
                  block
                  icon={<FireOutlined />}
                  onClick={() => navigate('/live')}
                >
                  直播监控
                </Button>
              </Col>
              <Col span={12}>
                <Button
                  block
                  icon={<ScheduleOutlined />}
                  onClick={() => navigate('/tasks')}
                >
                  任务管理
                </Button>
              </Col>
            </Row>
          </Card>

          <Card title="最近动态" bordered={false}>
            <Spin spinning={activitiesLoading}>
              {activities.length > 0 ? (
                <List
                  size="small"
                  dataSource={activities}
                  renderItem={(item) => (
                    <List.Item>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                        {getActivityIcon(item.icon)}
                        <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {item.text}
                        </span>
                      </div>
                      <span style={{ color: '#999', fontSize: 12, marginLeft: 8 }}>
                        {item.time ? formatTimeAgo(item.time) : ''}
                      </span>
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无动态，开始采集数据后这里会显示最近活动" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </Spin>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
