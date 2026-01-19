import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import {
  Row,
  Col,
  Card,
  Input,
  Button,
  Descriptions,
  Statistic,
  List,
  Tag,
  message,
  Spin,
  Empty,
  Avatar,
  Space,
  Divider,
} from 'antd'
import {
  SearchOutlined,
  PlayCircleOutlined,
  HeartOutlined,
  CommentOutlined,
  ShareAltOutlined,
  StarOutlined,
  DownloadOutlined,
  UserOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { videoApi } from '../services/api'
import { formatNumber, formatDate, formatDuration, extractIdFromUrl } from '../utils/format'

interface VideoDetail {
  id?: number
  aweme_id: string
  desc: string
  video_url: string
  cover_url: string
  music_url: string
  duration: number
  play_count: number
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  create_time: string
}

interface Comment {
  cid: string
  content: string
  digg_count: number
  reply_count: number
  user: {
    nickname: string
    avatar_url?: string
  }
  create_time: string
  ip_label: string
}

const VideoAnalysis = () => {
  const location = useLocation()
  const [searchValue, setSearchValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [video, setVideo] = useState<VideoDetail | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [loadingComments, setLoadingComments] = useState(false)

  useEffect(() => {
    const state = location.state as { url?: string; keyword?: string }
    if (state?.url) {
      setSearchValue(state.url)
      handleSearch(state.url)
    }
  }, [location])

  const handleSearch = async (value?: string) => {
    const searchInput = value || searchValue
    if (!searchInput.trim()) {
      message.warning('请输入视频链接或 aweme_id')
      return
    }

    setLoading(true)
    try {
      // Extract aweme_id from URL or use directly
      let awemeId = searchInput
      const extracted = extractIdFromUrl(searchInput)
      if (extracted?.type === 'video') {
        awemeId = extracted.id
      }

      // Try to parse URL first
      let videoData
      if (searchInput.includes('douyin.com')) {
        videoData = await videoApi.parse(searchInput)
      } else {
        videoData = await videoApi.getDetail(awemeId)
      }

      if (videoData) {
        setVideo(videoData as VideoDetail)
        // Fetch comments
        fetchComments(videoData.aweme_id)
      } else {
        message.error('视频不存在或获取失败')
      }
    } catch (error) {
      message.error('获取视频信息失败')
      // Mock data
      setVideo({
        aweme_id: '12345678901234567',
        desc: '这是一个示例视频描述 #热门 #推荐',
        video_url: '',
        cover_url: '',
        music_url: '',
        duration: 30,
        play_count: 1234567,
        digg_count: 98765,
        comment_count: 4321,
        share_count: 1234,
        collect_count: 5678,
        create_time: '2024-01-15',
      })
      setComments([
        {
          cid: '1',
          content: '太棒了！',
          digg_count: 100,
          reply_count: 5,
          user: { nickname: '用户A' },
          create_time: '2024-01-15',
          ip_label: '北京',
        },
        {
          cid: '2',
          content: '学到了！',
          digg_count: 50,
          reply_count: 2,
          user: { nickname: '用户B' },
          create_time: '2024-01-15',
          ip_label: '上海',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const fetchComments = async (awemeId: string) => {
    setLoadingComments(true)
    try {
      const data = await videoApi.getComments(awemeId, 0, 20)
      if (data?.comments) {
        setComments(data.comments)
      }
    } catch (error) {
      console.error('Failed to fetch comments:', error)
    } finally {
      setLoadingComments(false)
    }
  }

  const handleDownload = async () => {
    if (!video) return
    try {
      const result = await videoApi.download(video.aweme_id)
      if (result?.video_url) {
        window.open(result.video_url, '_blank')
        message.success('正在下载视频')
      }
    } catch (error) {
      message.error('下载失败')
    }
  }

  const getEngagementChartOption = () => ({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    xAxis: {
      type: 'category',
      data: ['点赞', '评论', '分享', '收藏'],
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        data: [
          video?.digg_count || 0,
          video?.comment_count || 0,
          video?.share_count || 0,
          video?.collect_count || 0,
        ],
        type: 'bar',
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            const colors = ['#ff4d4f', '#1890ff', '#52c41a', '#faad14']
            return colors[params.dataIndex]
          },
        },
      },
    ],
  })

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>视频分析</h2>

      {/* Search */}
      <Card bordered={false} style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col flex={1}>
            <Input
              size="large"
              placeholder="输入抖音视频链接或 aweme_id..."
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

      {/* Video Detail */}
      <Spin spinning={loading}>
        {video ? (
          <Row gutter={24}>
            <Col xs={24} lg={16}>
              {/* Video Info */}
              <Card bordered={false} style={{ marginBottom: 24 }}>
                <Row gutter={24}>
                  <Col span={8}>
                    <div
                      style={{
                        height: 300,
                        background: '#000',
                        borderRadius: 8,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        overflow: 'hidden',
                      }}
                    >
                      {video.cover_url ? (
                        <img
                          src={video.cover_url}
                          alt={video.desc}
                          style={{ maxWidth: '100%', maxHeight: '100%' }}
                        />
                      ) : (
                        <PlayCircleOutlined style={{ fontSize: 64, color: '#fff' }} />
                      )}
                    </div>
                  </Col>
                  <Col span={16}>
                    <div style={{ marginBottom: 16 }}>
                      <h3 style={{ marginBottom: 8 }}>{video.desc || '无描述'}</h3>
                      <Space>
                        <Tag>时长: {formatDuration(video.duration)}</Tag>
                        <Tag>发布于: {formatDate(video.create_time, 'YYYY-MM-DD')}</Tag>
                      </Space>
                    </div>

                    <Row gutter={16} style={{ marginBottom: 16 }}>
                      <Col span={8}>
                        <Statistic
                          title="播放量"
                          value={video.play_count}
                          formatter={(v) => formatNumber(v as number)}
                          prefix={<PlayCircleOutlined />}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="点赞"
                          value={video.digg_count}
                          formatter={(v) => formatNumber(v as number)}
                          prefix={<HeartOutlined />}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="评论"
                          value={video.comment_count}
                          formatter={(v) => formatNumber(v as number)}
                          prefix={<CommentOutlined />}
                        />
                      </Col>
                    </Row>

                    <Row gutter={16}>
                      <Col span={8}>
                        <Statistic
                          title="分享"
                          value={video.share_count}
                          formatter={(v) => formatNumber(v as number)}
                          prefix={<ShareAltOutlined />}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="收藏"
                          value={video.collect_count}
                          formatter={(v) => formatNumber(v as number)}
                          prefix={<StarOutlined />}
                        />
                      </Col>
                      <Col span={8}>
                        <Button
                          type="primary"
                          icon={<DownloadOutlined />}
                          onClick={handleDownload}
                          style={{ marginTop: 24 }}
                        >
                          下载视频
                        </Button>
                      </Col>
                    </Row>
                  </Col>
                </Row>
              </Card>

              {/* Comments */}
              <Card
                title={`评论 (${video.comment_count})`}
                bordered={false}
              >
                <Spin spinning={loadingComments}>
                  <List
                    dataSource={comments}
                    renderItem={(comment) => (
                      <List.Item
                        actions={[
                          <span key="like">
                            <HeartOutlined /> {comment.digg_count}
                          </span>,
                          <span key="reply">
                            <CommentOutlined /> {comment.reply_count}
                          </span>,
                        ]}
                      >
                        <List.Item.Meta
                          avatar={
                            <Avatar
                              icon={<UserOutlined />}
                              src={comment.user?.avatar_url}
                            />
                          }
                          title={
                            <Space>
                              <span>{comment.user?.nickname || '匿名用户'}</span>
                              {comment.ip_label && (
                                <Tag size="small">{comment.ip_label}</Tag>
                              )}
                            </Space>
                          }
                          description={comment.content}
                        />
                      </List.Item>
                    )}
                  />
                </Spin>
              </Card>
            </Col>

            {/* Stats */}
            <Col xs={24} lg={8}>
              <Card title="互动数据分析" bordered={false} style={{ marginBottom: 24 }}>
                <ReactECharts option={getEngagementChartOption()} style={{ height: 250 }} />
              </Card>

              <Card title="数据指标" bordered={false}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="互动率">
                    {video.play_count > 0
                      ? `${(
                          ((video.digg_count + video.comment_count + video.share_count) /
                            video.play_count) *
                          100
                        ).toFixed(2)}%`
                      : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="点赞率">
                    {video.play_count > 0
                      ? `${((video.digg_count / video.play_count) * 100).toFixed(2)}%`
                      : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="评论率">
                    {video.play_count > 0
                      ? `${((video.comment_count / video.play_count) * 100).toFixed(2)}%`
                      : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="分享率">
                    {video.play_count > 0
                      ? `${((video.share_count / video.play_count) * 100).toFixed(2)}%`
                      : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="收藏率">
                    {video.play_count > 0
                      ? `${((video.collect_count / video.play_count) * 100).toFixed(2)}%`
                      : '-'}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
          </Row>
        ) : (
          <Card bordered={false}>
            <Empty description="输入视频链接开始分析" />
          </Card>
        )}
      </Spin>
    </div>
  )
}

export default VideoAnalysis
