import { useState, useEffect } from 'react'
import { Card, Tabs, List, Tag, Spin, Row, Col } from 'antd'
import { FireOutlined, PlayCircleOutlined, VideoCameraOutlined } from '@ant-design/icons'
import { rankingApi, searchApi } from '../services/api'
import { formatNumber } from '../utils/format'

interface HotItem {
  word: string
  hot_value: number
  position: number
}

const HotRanking = () => {
  const [loading, setLoading] = useState(false)
  const [hotSearch, setHotSearch] = useState<HotItem[]>([])
  const [activeTab, setActiveTab] = useState('hot_search')

  useEffect(() => {
    fetchData()
  }, [activeTab])

  const fetchData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'hot_search') {
        const data = await searchApi.getTrending()
        setHotSearch(data?.trends || [])
      } else {
        const data = await rankingApi.getHotList(activeTab)
        setHotSearch(data?.items || [])
      }
    } catch {
      // Mock data
      setHotSearch(Array.from({ length: 50 }, (_, i) => ({
        word: `热搜话题${i + 1}`,
        hot_value: Math.floor(Math.random() * 1000000),
        position: i + 1,
      })))
    } finally {
      setLoading(false)
    }
  }

  const tabItems = [
    { key: 'hot_search', label: <><FireOutlined /> 热搜榜</>, icon: <FireOutlined /> },
    { key: 'hot_video', label: <><PlayCircleOutlined /> 视频榜</>, icon: <PlayCircleOutlined /> },
    { key: 'hot_live', label: <><VideoCameraOutlined /> 直播榜</>, icon: <VideoCameraOutlined /> },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>热榜中心</h2>

      <Card bordered={false}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />

        <Spin spinning={loading}>
          <List
            dataSource={hotSearch}
            renderItem={(item, index) => (
              <List.Item
                actions={[<span key="hot" style={{ color: '#999' }}>{formatNumber(item.hot_value)} 热度</span>]}
              >
                <List.Item.Meta
                  avatar={
                    <Tag color={index < 3 ? '#f5222d' : index < 10 ? '#fa8c16' : 'default'} style={{ width: 32, textAlign: 'center' }}>
                      {index + 1}
                    </Tag>
                  }
                  title={<a style={{ color: 'inherit' }}>{item.word}</a>}
                />
              </List.Item>
            )}
          />
        </Spin>
      </Card>
    </div>
  )
}

export default HotRanking
