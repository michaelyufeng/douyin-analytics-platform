import { useState } from 'react'
import { Card, Input, Button, Row, Col, Statistic, List, Tag, Empty, Spin, Avatar, Badge } from 'antd'
import { SearchOutlined, VideoCameraOutlined, TeamOutlined, HeartOutlined, UserOutlined } from '@ant-design/icons'
import { liveApi } from '../services/api'
import { formatNumber } from '../utils/format'

interface LiveInfo {
  room_id: string
  title: string
  cover_url: string
  user_count: number
  status: number
}

interface Danmaku {
  user_nickname: string
  content: string
  msg_type: string
  timestamp: string
}

const LiveMonitor = () => {
  const [searchValue, setSearchValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [liveInfo, setLiveInfo] = useState<LiveInfo | null>(null)
  const [danmaku, setDanmaku] = useState<Danmaku[]>([])

  const handleSearch = async () => {
    if (!searchValue.trim()) return
    setLoading(true)
    try {
      const data = await liveApi.getInfo(searchValue)
      setLiveInfo(data as LiveInfo)
      const dmData = await liveApi.getDanmaku(searchValue, 50)
      if (dmData?.danmaku) setDanmaku(dmData.danmaku)
    } catch {
      // Mock data
      setLiveInfo({
        room_id: '123456',
        title: '示例直播间',
        cover_url: '',
        user_count: 12345,
        status: 1,
      })
      setDanmaku([
        { user_nickname: '用户A', content: '主播好', msg_type: 'chat', timestamp: new Date().toISOString() },
        { user_nickname: '用户B', content: '666', msg_type: 'chat', timestamp: new Date().toISOString() },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>直播监控</h2>

      <Card bordered={false} style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col flex={1}>
            <Input
              size="large"
              placeholder="输入直播间链接或 room_id..."
              prefix={<SearchOutlined />}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onPressEnter={handleSearch}
            />
          </Col>
          <Col>
            <Button type="primary" size="large" onClick={handleSearch} loading={loading}>
              监控
            </Button>
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        {liveInfo ? (
          <Row gutter={24}>
            <Col xs={24} lg={16}>
              <Card bordered={false} style={{ marginBottom: 24 }}>
                <Row gutter={24} align="middle">
                  <Col>
                    <div style={{ width: 120, height: 160, background: '#000', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {liveInfo.cover_url ? (
                        <img src={liveInfo.cover_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      ) : (
                        <VideoCameraOutlined style={{ fontSize: 48, color: '#fff' }} />
                      )}
                    </div>
                  </Col>
                  <Col flex={1}>
                    <Badge status={liveInfo.status === 1 ? 'processing' : 'default'} text={liveInfo.status === 1 ? '直播中' : '未开播'} />
                    <h3 style={{ margin: '8px 0' }}>{liveInfo.title || '直播间'}</h3>
                    <Row gutter={24}>
                      <Col><Statistic title="在线人数" value={liveInfo.user_count} prefix={<TeamOutlined />} /></Col>
                    </Row>
                  </Col>
                </Row>
              </Card>

              <Card title="实时弹幕" bordered={false}>
                <List
                  dataSource={danmaku}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<Avatar icon={<UserOutlined />} />}
                        title={item.user_nickname}
                        description={item.content}
                      />
                      <Tag>{item.msg_type}</Tag>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card title="直播统计" bordered={false}>
                <Statistic title="当前在线" value={formatNumber(liveInfo.user_count)} prefix={<TeamOutlined />} style={{ marginBottom: 24 }} />
                <Button type="primary" block>开始录制</Button>
              </Card>
            </Col>
          </Row>
        ) : (
          <Card bordered={false}><Empty description="输入直播间链接开始监控" /></Card>
        )}
      </Spin>
    </div>
  )
}

export default LiveMonitor
