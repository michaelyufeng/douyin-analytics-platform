import { useState, useEffect, useRef } from 'react'
import { Card, Form, Input, Button, Switch, InputNumber, Divider, message, Row, Col, Modal, Spin, Tag, Alert, Tabs, Typography, Steps } from 'antd'
import { SaveOutlined, QrcodeOutlined, CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined, DownloadOutlined, CodeOutlined, CopyOutlined, CloudUploadOutlined, GlobalOutlined } from '@ant-design/icons'
import { authApi } from '../services/api'

const { Text, Paragraph } = Typography
const { TextArea } = Input

interface CookieStatus {
  has_cookie: boolean
  cookie_preview: string | null
  message: string
}

interface ConsoleCommandData {
  command: string
  instructions: string[]
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
  const [consoleCommand, setConsoleCommand] = useState<ConsoleCommandData | null>(null)
  const [activeTab, setActiveTab] = useState<string>('qrcode')  // Online scanning as default
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Get server URL from current location
  const serverUrl = `${window.location.protocol}//${window.location.host}`

  useEffect(() => {
    checkCookieStatus()
    loadConsoleCommand()
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

  const loadConsoleCommand = async () => {
    try {
      const data = await authApi.getConsoleCommand()
      setConsoleCommand(data)
    } catch (error) {
      console.error('Failed to load console command:', error)
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

  const downloadScript = async () => {
    try {
      const scriptContent = await authApi.getScript()
      const blob = new Blob([scriptContent], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'get_cookie.py'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      message.success('脚本下载成功')
    } catch (error) {
      message.error('下载失败，请重试')
      console.error('Download error:', error)
    }
  }

  const downloadScriptAuto = async () => {
    try {
      const scriptContent = await authApi.getScriptAuto()
      const blob = new Blob([scriptContent], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'get_cookie_auto.py'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      message.success('脚本下载成功')
    } catch (error) {
      message.error('下载失败，请重试')
      console.error('Download error:', error)
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      message.success('已复制到剪贴板')
    } catch {
      message.error('复制失败，请手动复制')
    }
  }

  // Tab content for QR Code login - Primary recommended method
  const QRCodeTabContent = (
    <div>
      <Alert
        type="success"
        message="推荐方式 - 扫码登录"
        description="点击按钮后，用抖音 App 扫描二维码即可完成登录。服务器已优化反检测机制，支持虚拟显示。"
        style={{ marginBottom: 16 }}
      />
      <Button
        type="primary"
        icon={<QrcodeOutlined />}
        onClick={() => {
          setQrModalOpen(true)
          startQRLogin()
        }}
        style={{ width: '100%', height: 48 }}
        size="large"
      >
        立即扫码登录
      </Button>
    </div>
  )

  // Tab content for Local Script (Auto Upload Version) - Backup option
  const LocalScriptTabContent = (
    <div>
      <Alert
        type="info"
        message="备选方案 - 本地脚本"
        description="如果在线扫码无法使用，可下载脚本到本地运行，扫码后 Cookie 会自动上传到服务器。"
        style={{ marginBottom: 16 }}
      />

      {/* Server URL Display */}
      <div style={{
        background: '#f5f5f5',
        padding: 12,
        borderRadius: 4,
        marginBottom: 16,
        display: 'flex',
        alignItems: 'center',
        gap: 8
      }}>
        <GlobalOutlined style={{ color: '#1890ff' }} />
        <Text strong>服务器地址:</Text>
        <Text code copyable>{serverUrl}</Text>
      </div>

      <Steps
        direction="vertical"
        size="small"
        current={-1}
        items={[
          { title: '下载脚本', description: '点击下方按钮下载 get_cookie_auto.py' },
          { title: '安装依赖', description: <Text code>pip install playwright httpx && playwright install chromium</Text> },
          { title: '运行脚本', description: <span>运行: <Text code copyable={{ text: `python get_cookie_auto.py --server ${serverUrl}` }}>python get_cookie_auto.py --server {serverUrl}</Text></span> },
          { title: '扫码登录', description: '用抖音 App 扫描浏览器中的二维码' },
          { title: '自动完成', description: '登录成功后 Cookie 会自动上传到服务器' },
        ]}
        style={{ marginBottom: 16 }}
      />
      <div style={{ display: 'flex', gap: 8 }}>
        <Button
          type="primary"
          icon={<CloudUploadOutlined />}
          onClick={downloadScriptAuto}
          style={{ flex: 1 }}
          size="large"
        >
          下载自动上传脚本
        </Button>
        <Button
          icon={<DownloadOutlined />}
          onClick={downloadScript}
          size="large"
          title="下载基础版本 (需手动复制粘贴)"
        >
          基础版
        </Button>
      </div>
    </div>
  )

  // Tab content for Browser Console
  const ConsoleTabContent = (
    <div>
      <Alert
        type="warning"
        message="浏览器控制台方式"
        description="如果您已经在浏览器中登录了抖音，可以使用控制台命令快速提取 Cookie。"
        style={{ marginBottom: 16 }}
      />
      {consoleCommand && (
        <>
          <Steps
            direction="vertical"
            size="small"
            current={-1}
            items={consoleCommand.instructions.map((instruction, index) => ({
              title: `步骤 ${index + 1}`,
              description: instruction,
            }))}
            style={{ marginBottom: 16 }}
          />
          <div style={{ marginBottom: 16 }}>
            <Text strong>控制台命令：</Text>
            <div style={{
              background: '#1e1e1e',
              padding: 12,
              borderRadius: 4,
              marginTop: 8,
              position: 'relative'
            }}>
              <Paragraph
                style={{
                  color: '#d4d4d4',
                  fontFamily: 'monospace',
                  fontSize: 12,
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all'
                }}
              >
                {consoleCommand.command}
              </Paragraph>
              <Button
                icon={<CopyOutlined />}
                size="small"
                onClick={() => copyToClipboard(consoleCommand.command)}
                style={{ position: 'absolute', top: 8, right: 8 }}
              >
                复制
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )

  // Tab content for Manual Input
  const ManualTabContent = (
    <div>
      <Alert
        type="info"
        message="手动粘贴 Cookie"
        description="从浏览器开发者工具中复制 Cookie，然后粘贴到下方输入框。"
        style={{ marginBottom: 16 }}
      />
      <Steps
        direction="vertical"
        size="small"
        current={-1}
        items={[
          { title: '打开抖音', description: '在浏览器中访问 https://www.douyin.com 并登录' },
          { title: '打开开发者工具', description: '按 F12 打开开发者工具' },
          { title: '找到 Cookie', description: '切换到 Network 标签，刷新页面，点击任意请求查看 Headers 中的 Cookie' },
          { title: '复制 Cookie', description: '复制完整的 Cookie 字符串' },
        ]}
        style={{ marginBottom: 16 }}
      />
    </div>
  )

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
                  description={cookieStatus.cookie_preview ? `当前 Cookie: ${cookieStatus.cookie_preview}` : '请通过以下方式获取 Cookie'}
                  style={{ marginBottom: 16 }}
                />
              )}

              {/* Cookie Acquisition Methods */}
              <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                items={[
                  {
                    key: 'qrcode',
                    label: (
                      <span>
                        <QrcodeOutlined />
                        扫码登录 (推荐)
                      </span>
                    ),
                    children: QRCodeTabContent,
                  },
                  {
                    key: 'script',
                    label: (
                      <span>
                        <CodeOutlined />
                        本地脚本
                      </span>
                    ),
                    children: LocalScriptTabContent,
                  },
                  {
                    key: 'console',
                    label: (
                      <span>
                        <CodeOutlined />
                        控制台
                      </span>
                    ),
                    children: ConsoleTabContent,
                  },
                  {
                    key: 'manual',
                    label: '手动粘贴',
                    children: ManualTabContent,
                  },
                ]}
              />

              <Divider>Cookie 输入</Divider>

              <Form.Item
                name="cookie"
                label="抖音 Cookie"
                extra="将获取到的 Cookie 粘贴到此处"
              >
                <TextArea rows={4} placeholder="粘贴抖音 Cookie..." />
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
              <Alert
                type="info"
                message="Cookie 获取方式说明"
                description={
                  <ul style={{ paddingLeft: 20, margin: '8px 0' }}>
                    <li><strong>扫码登录 (推荐)</strong>: 点击按钮，用抖音 App 扫码即可</li>
                    <li><strong>本地脚本</strong>: 扫码失败时的备选方案</li>
                    <li><strong>控制台命令</strong>: 适合已登录用户快速提取</li>
                    <li><strong>手动粘贴</strong>: 通用方式，需要手动操作</li>
                  </ul>
                }
                style={{ marginBottom: 16 }}
              />
              <Alert
                type="success"
                message="服务器已优化"
                description={
                  <div>
                    <p style={{ margin: '4px 0' }}>服务器已配置 xvfb 虚拟显示和反检测机制，支持直接扫码登录。</p>
                    <p style={{ margin: '4px 0' }}>如果扫码仍然失败，可尝试使用「本地脚本」备选方案。</p>
                  </div>
                }
              />
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
              {(loginStatus === 'error' || loginStatus === 'expired') && (
                <Alert
                  type="warning"
                  message="如果扫码失败，建议使用「本地脚本」方式获取 Cookie"
                  style={{ marginTop: 16, textAlign: 'left' }}
                />
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
