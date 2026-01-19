import { useState, useEffect, useRef } from 'react'
import { Card, Form, Input, Button, Switch, InputNumber, Divider, message, Row, Col, Modal, Spin, Tag, Alert } from 'antd'
import { SaveOutlined, QrcodeOutlined, CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import { authApi } from '../services/api'

interface CookieStatus {
  has_cookie: boolean
  cookie_preview: string | null
  message: string
}

const Settings = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [qrModalOpen, setQrModalOpen] = useState(false)
  const [qrLoading, setQrLoading] = useState(false)
  const [qrImage, setQrImage] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [loginStatus, setLoginStatus] = useState<string>('idle')
  const [statusMessage, setStatusMessage] = useState<string>('')
  const [cookieStatus, setCookieStatus] = useState<CookieStatus | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    checkCookieStatus()
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  const checkCookieStatus = async () => {
    try {
      const status = await authApi.getCookieStatus()
      setCookieStatus(status)
    } catch (error) {
      console.error('Failed to check cookie status:', error)
    }
  }

  const handleSave = async (values: Record<string, unknown>) => {
    setLoading(true)
    try {
      // Save cookie to backend
      if (values.cookie) {
        const result = await authApi.saveCookie(values.cookie as string)
        if (result.success) {
          message.success('Cookie 保存成功')
          checkCookieStatus()
        } else {
          message.error(result.message || '保存失败')
        }
      }
      // Save other settings to localStorage
      localStorage.setItem('douyin_settings', JSON.stringify(values))
      message.success('设置已保存')
    } catch {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  const startQRLogin = async () => {
    setQrLoading(true)
    setLoginStatus('loading')
    setStatusMessage('正在生成二维码...')
    setQrImage(null)

    try {
      const result = await authApi.createQRCode()

      if (result.success && result.qr_image) {
        setQrImage(result.qr_image)
        setSessionId(result.session_id || null)
        setLoginStatus('waiting')
        setStatusMessage(result.message || '请使用抖音 App 扫描二维码')

        // Start polling for login status
        if (result.session_id) {
          startPolling(result.session_id)
        }
      } else {
        setLoginStatus('error')
        setStatusMessage(result.message || result.error || '生成二维码失败')
      }
    } catch (error) {
      setLoginStatus('error')
      setStatusMessage('生成二维码失败，请确保服务器已正确配置')
      console.error('QR login error:', error)
    } finally {
      setQrLoading(false)
    }
  }

  const startPolling = (sid: string) => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
    }

    pollingRef.current = setInterval(async () => {
      try {
        const status = await authApi.checkQRStatus(sid)

        if (status.status === 'success') {
          setLoginStatus('success')
          setStatusMessage(status.message || '登录成功！')
          stopPolling()
          message.success('登录成功！Cookie 已自动保存')
          checkCookieStatus()
          setTimeout(() => setQrModalOpen(false), 2000)
        } else if (status.status === 'expired') {
          setLoginStatus('expired')
          setStatusMessage(status.message || '二维码已过期')
          stopPolling()
        } else if (status.status === 'error') {
          setLoginStatus('error')
          setStatusMessage(status.message || '登录出错')
          stopPolling()
        }
        // Continue polling if status is 'waiting'
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 2000) // Poll every 2 seconds
  }

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  const handleModalClose = () => {
    stopPolling()
    if (sessionId) {
      authApi.cancelQRLogin(sessionId).catch(console.error)
    }
    setQrModalOpen(false)
    setQrImage(null)
    setSessionId(null)
    setLoginStatus('idle')
  }

  const getStatusIcon = () => {
    switch (loginStatus) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 24 }} />
      case 'error':
      case 'expired':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 24 }} />
      default:
        return null
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
            <Card
              title="Cookie 配置"
              bordered={false}
              style={{ marginBottom: 24 }}
              extra={
                cookieStatus?.has_cookie ? (
                  <Tag color="success" icon={<CheckCircleOutlined />}>已配置</Tag>
                ) : (
                  <Tag color="warning">未配置</Tag>
                )
              }
            >
              {/* Cookie Status */}
              {cookieStatus && (
                <Alert
                  type={cookieStatus.has_cookie ? 'success' : 'warning'}
                  message={cookieStatus.message}
                  description={cookieStatus.cookie_preview ? `当前 Cookie: ${cookieStatus.cookie_preview}` : '请通过扫码登录或手动粘贴 Cookie'}
                  style={{ marginBottom: 16 }}
                />
              )}

              {/* QR Code Login Button */}
              <Button
                type="primary"
                icon={<QrcodeOutlined />}
                onClick={() => {
                  setQrModalOpen(true)
                  startQRLogin()
                }}
                style={{ marginBottom: 16, width: '100%' }}
                size="large"
              >
                扫码登录抖音
              </Button>

              <Divider>或手动配置</Divider>

              <Form.Item
                name="cookie"
                label="抖音 Cookie"
                extra="从浏览器开发者工具 (F12 -> Network -> 任意请求的 Headers) 中复制 Cookie"
              >
                <Input.TextArea rows={4} placeholder="粘贴抖音 Cookie..." />
              </Form.Item>

              <Button type="default" htmlType="submit" loading={loading} style={{ width: '100%' }}>
                保存 Cookie
              </Button>
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

            <Card title="使用说明" bordered={false}>
              <ol style={{ paddingLeft: 20, margin: 0, lineHeight: 2 }}>
                <li>点击「扫码登录抖音」按钮</li>
                <li>使用抖音 App 扫描显示的二维码</li>
                <li>在手机上确认登录</li>
                <li>系统会自动获取并保存 Cookie</li>
                <li>如扫码失败，可手动从浏览器复制 Cookie</li>
              </ol>
            </Card>
          </Col>
        </Row>

        <Divider />

        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
            保存所有设置
          </Button>
        </Form.Item>
      </Form>

      {/* QR Code Modal */}
      <Modal
        title="扫码登录抖音"
        open={qrModalOpen}
        onCancel={handleModalClose}
        footer={[
          <Button key="cancel" onClick={handleModalClose}>
            取消
          </Button>,
          <Button
            key="refresh"
            type="primary"
            icon={<ReloadOutlined />}
            onClick={startQRLogin}
            loading={qrLoading}
            disabled={loginStatus === 'success'}
          >
            刷新二维码
          </Button>
        ]}
        width={400}
        centered
      >
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          {qrLoading ? (
            <Spin size="large" tip="正在生成二维码..." />
          ) : qrImage ? (
            <>
              <div style={{
                marginBottom: 16,
                padding: 16,
                background: '#fff',
                display: 'inline-block',
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}>
                <img
                  src={`data:image/png;base64,${qrImage}`}
                  alt="QR Code"
                  style={{ width: 200, height: 200 }}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                {getStatusIcon()}
                <span style={{
                  color: loginStatus === 'success' ? '#52c41a' :
                         loginStatus === 'error' || loginStatus === 'expired' ? '#ff4d4f' :
                         '#666'
                }}>
                  {statusMessage}
                </span>
              </div>
              {loginStatus === 'waiting' && (
                <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
                  请使用抖音 App 扫描上方二维码
                </div>
              )}
            </>
          ) : (
            <div style={{ color: '#ff4d4f' }}>
              {statusMessage || '加载失败，请重试'}
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

export default Settings
