import { useState } from 'react'
import { Card, Input, Button, Row, Col, Statistic, List, Tag, Empty, Spin, Progress } from 'antd'
import { SearchOutlined, SmileOutlined, MehOutlined, FrownOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { videoApi, analysisApi } from '../services/api'

const CommentAnalysis = () => {
  const [searchValue, setSearchValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<{
    total_comments: number
    sentiment: { positive: number; negative: number; neutral: number }
    top_keywords: { word: string; count: number }[]
  } | null>(null)

  const handleAnalyze = async () => {
    if (!searchValue.trim()) return
    setLoading(true)
    try {
      const data = await analysisApi.analyzeComments(searchValue)
      setAnalysis(data as typeof analysis)
    } catch {
      // Mock data
      setAnalysis({
        total_comments: 1234,
        sentiment: { positive: 0.65, negative: 0.1, neutral: 0.25 },
        top_keywords: [
          { word: '好看', count: 120 },
          { word: '喜欢', count: 98 },
          { word: '厉害', count: 76 },
          { word: '学到了', count: 54 },
        ],
      })
    } finally {
      setLoading(false)
    }
  }

  const getPieOption = () => ({
    tooltip: { trigger: 'item' },
    legend: { bottom: '0%' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: (analysis?.sentiment.positive || 0) * 100, name: '正面', itemStyle: { color: '#52c41a' } },
          { value: (analysis?.sentiment.neutral || 0) * 100, name: '中性', itemStyle: { color: '#faad14' } },
          { value: (analysis?.sentiment.negative || 0) * 100, name: '负面', itemStyle: { color: '#ff4d4f' } },
        ],
      },
    ],
  })

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>评论分析</h2>

      <Card bordered={false} style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col flex={1}>
            <Input
              size="large"
              placeholder="输入视频链接或 aweme_id 进行评论分析..."
              prefix={<SearchOutlined />}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onPressEnter={handleAnalyze}
            />
          </Col>
          <Col>
            <Button type="primary" size="large" onClick={handleAnalyze} loading={loading}>
              分析评论
            </Button>
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        {analysis ? (
          <Row gutter={24}>
            <Col xs={24} lg={12}>
              <Card title="情感分析" bordered={false} style={{ marginBottom: 24 }}>
                <ReactECharts option={getPieOption()} style={{ height: 300 }} />
                <Row gutter={16} style={{ marginTop: 16 }}>
                  <Col span={8}>
                    <Statistic
                      title={<><SmileOutlined style={{ color: '#52c41a' }} /> 正面</>}
                      value={analysis.sentiment.positive * 100}
                      suffix="%"
                      precision={1}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title={<><MehOutlined style={{ color: '#faad14' }} /> 中性</>}
                      value={analysis.sentiment.neutral * 100}
                      suffix="%"
                      precision={1}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title={<><FrownOutlined style={{ color: '#ff4d4f' }} /> 负面</>}
                      value={analysis.sentiment.negative * 100}
                      suffix="%"
                      precision={1}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title={`评论统计 (共${analysis.total_comments}条)`} bordered={false} style={{ marginBottom: 24 }}>
                <List
                  header="高频词"
                  dataSource={analysis.top_keywords}
                  renderItem={(item) => (
                    <List.Item>
                      <span>{item.word}</span>
                      <Progress percent={(item.count / (analysis.top_keywords[0]?.count || 1)) * 100} showInfo={false} style={{ width: 100 }} />
                      <Tag>{item.count}</Tag>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        ) : (
          <Card bordered={false}><Empty description="输入视频链接开始分析评论" /></Card>
        )}
      </Spin>
    </div>
  )
}

export default CommentAnalysis
