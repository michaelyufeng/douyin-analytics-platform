import { useState } from 'react'
import { Card, Form, Input, Button, Switch, InputNumber, Divider, message, Row, Col } from 'antd'
import { SaveOutlined } from '@ant-design/icons'

const Settings = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSave = async (values: Record<string, unknown>) => {
    setLoading(true)
    try {
      // Save to localStorage for demo
      localStorage.setItem('douyin_settings', JSON.stringify(values))
      message.success('设置已保存')
    } catch {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>系统设置</h2>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        initialValues={{
          cookie: '',
          proxy: '',
          requestTimeout: 30,
          maxRetries: 3,
          enableRedis: false,
          enableScheduler: true,
          monitorInterval: 3600,
        }}
      >
        <Row gutter={24}>
          <Col xs={24} lg={12}>
            <Card title="Cookie 配置" bordered={false} style={{ marginBottom: 24 }}>
              <Form.Item
                name="cookie"
                label="抖音 Cookie"
                extra="从浏览器开发者工具中获取"
              >
                <Input.TextArea rows={4} placeholder="粘贴抖音 Cookie..." />
              </Form.Item>
            </Card>

            <Card title="代理设置" bordered={false} style={{ marginBottom: 24 }}>
              <Form.Item name="proxy" label="HTTP 代理" extra="格式: http://host:port">
                <Input placeholder="http://127.0.0.1:7890" />
              </Form.Item>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="请求配置" bordered={false} style={{ marginBottom: 24 }}>
              <Form.Item name="requestTimeout" label="请求超时 (秒)">
                <InputNumber min={5} max={120} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="maxRetries" label="最大重试次数">
                <InputNumber min={0} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Card>

            <Card title="服务配置" bordered={false} style={{ marginBottom: 24 }}>
              <Form.Item name="enableRedis" label="启用 Redis 缓存" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Form.Item name="enableScheduler" label="启用定时任务" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Form.Item name="monitorInterval" label="默认监控间隔 (秒)">
                <InputNumber min={60} style={{ width: '100%' }} />
              </Form.Item>
            </Card>
          </Col>
        </Row>

        <Divider />

        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
            保存设置
          </Button>
        </Form.Item>
      </Form>
    </div>
  )
}

export default Settings
