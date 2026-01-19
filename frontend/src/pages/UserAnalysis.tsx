import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import {
  Row,
  Col,
  Card,
  Input,
  Button,
  Avatar,
  Descriptions,
  Statistic,
  List,
  Tabs,
  Tag,
  message,
  Spin,
  Empty,
  Space,
} from 'antd'
import {
  SearchOutlined,
  UserOutlined,
  HeartOutlined,
  TeamOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { userApi } from '../services/api'
import { formatNumber, extractIdFromUrl } from '../utils/format'

interface UserProfile {
  id: number
  sec_uid: string
  nickname: string
  unique_id: string
  avatar_url: string
  signature: string
  follower_count: number
  following_count: number
  total_favorited: number
  aweme_count: number
  is_verified: boolean
  verify_info: string
  region: string
}

interface Video {
  aweme_id: string
  desc: string
  cover_url: string
  play_count: number
  digg_count: number
  comment_count: number
  share_count: number
  create_time: string
}

const UserAnalysis = () => {
  const location = useLocation()
  const [searchValue, setSearchValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState<UserProfile | null>(null)
  const [videos, setVideos] = useState<Video[]>([])
  const [activeTab, setActiveTab] = useState('posts')

  useEffect(() => {
    // Check if URL was passed via navigation
    const state = location.state as { url?: string }
    if (state?.url) {
      setSearchValue(state.url)
      handleSearch(state.url)
    }
  }, [location])

  const handleSearch = async (value?: string) => {
    const searchInput = value || searchValue
    if (!searchInput.trim()) {
      message.warning('请输入用户主页链接或 sec_uid')
      return
    }

    setLoading(true)
    try {
      // Extract sec_uid from URL or use directly
      let secUid = searchInput
      const extracted = extractIdFromUrl(searchInput)
      if (extracted?.type === 'user') {
        secUid = extracted.id
      }

      const userData = await userApi.getProfile(secUid)
      if (userData) {
        setUser(userData as UserProfile)
        // Fetch user posts
        const postsData = await userApi.getPosts(secUid, 0, 20)
        if (postsData?.videos) {
          setVideos(postsData.videos)
        }
      } else {
        message.error('用户不存在或获取失败')
      }
    } catch (error) {
      message.error('获取用户信息失败')
      // Mock data for demo
      setUser({
        id: 1,
        sec_uid: 'MS4wLjABAAAAtest',
        nickname: '示例用户',
        unique_id: 'demo_user',
        avatar_url: '',
        signature: '这是一个示例用户签名',
        follower_count: 1234567,
        following_count: 123,
        total_favorited: 9876543,
        aweme_count: 100,
        is_verified: true,
        verify_info: '知名博主',
        region: '北京',
      })
      setVideos([
        {
          aweme_id: '1',
          desc: '示例视频1',
          cover_url: '',
          play_count: 100000,
          digg_count: 5000,
          comment_count: 200,
          share_count: 50,
          create_time: '2024-01-01',
        },
        {
          aweme_id: '2',
          desc: '示例视频2',
          cover_url: '',
          play_count: 200000,
          digg_count: 10000,
          comment_count: 500,
          share_count: 100,
          create_time: '2024-01-02',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const getChartOption = () => ({
    tooltip: {
      trigger: 'item',
    },
    legend: {
      bottom: '0%',
    },
    series: [
      {
        name: '互动数据',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data: [
          { value: user?.follower_count || 0, name: '粉丝' },
          { value: user?.following_count || 0, name: '关注' },
          { value: user?.total_favorited || 0, name: '获赞' },
        ],
      },
    ],
  })

  const tabItems = [
    {
      key: 'posts',
      label: (
        <span>
          <PlayCircleOutlined />
          作品 {user?.aweme_count || 0}
        </span>
      ),
      children: (
        <List
          grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }}
          dataSource={videos}
          renderItem={(video) => (
            <List.Item>
              <Card
                hoverable
                cover={
                  <div
                    style={{
                      height: 200,
                      background: '#f0f0f0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {video.cover_url ? (
                      <img
                        src={video.cover_url}
                        alt={video.desc}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <PlayCircleOutlined style={{ fontSize: 48, color: '#999' }} />
                    )}
                  </div>
                }
                bodyStyle={{ padding: 12 }}
              >
                <div style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>
                  {video.desc?.slice(0, 30) || '无描述'}
                </div>
                <Space size={16}>
                  <span><PlayCircleOutlined /> {formatNumber(video.play_count)}</span>
                  <span><HeartOutlined /> {formatNumber(video.digg_count)}</span>
                </Space>
              </Card>
            </List.Item>
          )}
        />
      ),
    },
    {
      key: 'likes',
      label: (
        <span>
          <HeartOutlined />
          喜欢
        </span>
      ),
      children: <Empty description="暂无数据" />,
    },
    {
      key: 'analysis',
      label: (
        <span>
          <CheckCircleOutlined />
          深度分析
        </span>
      ),
      children: (
        <Row gutter={16}>
          <Col span={12}>
            <Card title="互动数据分布" bordered={false}>
              <ReactECharts option={getChartOption()} style={{ height: 300 }} />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="账号分析" bordered={false}>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="平均播放量">
                  {videos.length > 0
                    ? formatNumber(
                        videos.reduce((sum, v) => sum + v.play_count, 0) / videos.length
                      )
                    : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="平均点赞">
                  {videos.length > 0
                    ? formatNumber(
                        videos.reduce((sum, v) => sum + v.digg_count, 0) / videos.length
                      )
                    : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="互动率">
                  {user && videos.length > 0
                    ? `${(
                        ((videos.reduce((sum, v) => sum + v.digg_count + v.comment_count, 0) /
                          videos.length /
                          (user.follower_count || 1)) *
                          100)
                      ).toFixed(2)}%`
                    : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="发布频率">
                  {user?.aweme_count ? `${(user.aweme_count / 30).toFixed(1)} 条/月` : '-'}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>
        </Row>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>用户分析</h2>

      {/* Search */}
      <Card bordered={false} style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col flex={1}>
            <Input
              size="large"
              placeholder="输入抖音用户主页链接或 sec_uid..."
              prefix={<SearchOutlined />}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onPressEnter={() => handleSearch()}
            />
          </Col>
          <Col>
            <Button
              type="primary"
              size="large"
              icon={<SearchOutlined />}
              onClick={() => handleSearch()}
              loading={loading}
            >
              分析
            </Button>
          </Col>
        </Row>
      </Card>

      {/* User Profile */}
      <Spin spinning={loading}>
        {user ? (
          <>
            <Card bordered={false} style={{ marginBottom: 24 }}>
              <Row gutter={24} align="middle">
                <Col>
                  <Avatar
                    size={100}
                    icon={<UserOutlined />}
                    src={user.avatar_url}
                  />
                </Col>
                <Col flex={1}>
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ fontSize: 24, fontWeight: 600, marginRight: 12 }}>
                      {user.nickname}
                    </span>
                    {user.is_verified && (
                      <Tag color="blue">
                        <CheckCircleOutlined /> {user.verify_info || '已认证'}
                      </Tag>
                    )}
                  </div>
                  <div style={{ color: '#666', marginBottom: 8 }}>
                    抖音号: {user.unique_id || '-'} | {user.region || '未知地区'}
                  </div>
                  <div style={{ color: '#999' }}>{user.signature || '暂无签名'}</div>
                </Col>
                <Col>
                  <Button type="primary" icon={<PlusOutlined />}>
                    添加监控
                  </Button>
                </Col>
              </Row>

              <Row gutter={24} style={{ marginTop: 24 }}>
                <Col span={6}>
                  <Statistic
                    title="粉丝"
                    value={user.follower_count}
                    formatter={(value) => formatNumber(value as number)}
                    prefix={<TeamOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="关注"
                    value={user.following_count}
                    formatter={(value) => formatNumber(value as number)}
                    prefix={<UserOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="获赞"
                    value={user.total_favorited}
                    formatter={(value) => formatNumber(value as number)}
                    prefix={<HeartOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="作品"
                    value={user.aweme_count}
                    prefix={<PlayCircleOutlined />}
                  />
                </Col>
              </Row>
            </Card>

            {/* Tabs */}
            <Card bordered={false}>
              <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                items={tabItems}
              />
            </Card>
          </>
        ) : (
          <Card bordered={false}>
            <Empty description="输入用户链接开始分析" />
          </Card>
        )}
      </Spin>
    </div>
  )
}

export default UserAnalysis
