import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, List, Tag, Input, Button, message, Spin } from 'antd'
import {
  UserOutlined,
  PlayCircleOutlined,
  FireOutlined,
  ScheduleOutlined,
  SearchOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { rankingApi, searchApi } from '../services/api'
import { formatNumber } from '../utils/format'

interface HotItem {
  word: string
  hot_value: number
  position: number
}

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  color: string
  suffix?: string
}

const StatCard = ({ title, value, icon, color, suffix }: StatCardProps) => (
  <Card className="hover-card" bordered={false}>
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
  </Card>
)

const Dashboard = () => {
  const navigate = useNavigate()
  const [searchValue, setSearchValue] = useState('')
  const [hotList, setHotList] = useState<HotItem[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({
    users: 128,
    videos: 1024,
    tasks: 12,
    hotItems: 50,
  })

  useEffect(() => {
    fetchHotList()
  }, [])

  const fetchHotList = async () => {
    setLoading(true)
    try {
      const data = await searchApi.getTrending()
      if (data?.trends) {
        setHotList(data.trends.slice(0, 20))
      }
    } catch (error) {
      // Use mock data if API fails
      setHotList([
        { word: '热搜话题1', hot_value: 1234567, position: 1 },
        { word: '热搜话题2', hot_value: 987654, position: 2 },
        { word: '热搜话题3', hot_value: 876543, position: 3 },
        { word: '热搜话题4', hot_value: 765432, position: 4 },
        { word: '热搜话题5', hot_value: 654321, position: 5 },
      ])
    } finally {
      setLoading(false)
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
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="已采集视频"
            value={stats.videos}
            icon={<PlayCircleOutlined />}
            color="#52c41a"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="监控任务"
            value={stats.tasks}
            icon={<ScheduleOutlined />}
            color="#faad14"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="今日热榜"
            value={stats.hotItems}
            icon={<FireOutlined />}
            color="#f5222d"
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
            <List
              size="small"
              dataSource={[
                { text: '用户 @xxx 粉丝数增长 1.2万', time: '2分钟前', type: 'up' },
                { text: '视频 #xxx 播放量突破 100万', time: '15分钟前', type: 'up' },
                { text: '监控任务 #3 执行完成', time: '1小时前', type: 'task' },
                { text: '用户 @yyy 粉丝数下降 0.5万', time: '2小时前', type: 'down' },
              ]}
              renderItem={(item) => (
                <List.Item>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {item.type === 'up' && <ArrowUpOutlined style={{ color: '#52c41a' }} />}
                    {item.type === 'down' && <ArrowDownOutlined style={{ color: '#f5222d' }} />}
                    {item.type === 'task' && <ScheduleOutlined style={{ color: '#1890ff' }} />}
                    <span>{item.text}</span>
                  </div>
                  <span style={{ color: '#999', fontSize: 12 }}>{item.time}</span>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
