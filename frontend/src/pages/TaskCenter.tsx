import { useState, useEffect } from 'react'
import { Card, Table, Button, Modal, Form, Input, Select, InputNumber, Tag, Space, message, Popconfirm } from 'antd'
import { PlusOutlined, PlayCircleOutlined, DeleteOutlined } from '@ant-design/icons'
import { taskApi } from '../services/api'
import { formatDate } from '../utils/format'

interface Task {
  id: number
  task_type: string
  target_id: string
  target_name: string
  interval_seconds: number
  is_active: boolean
  last_run: string | null
  next_run: string | null
  created_at: string
}

const TaskCenter = () => {
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState<Task[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchTasks()
  }, [])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const data = await taskApi.getTasks(0, 100)
      setTasks(data?.tasks || [])
    } catch {
      // Mock data
      setTasks([
        { id: 1, task_type: 'user', target_id: 'xxx', target_name: '用户A', interval_seconds: 3600, is_active: true, last_run: null, next_run: null, created_at: new Date().toISOString() },
        { id: 2, task_type: 'video', target_id: 'yyy', target_name: '视频B', interval_seconds: 1800, is_active: false, last_run: null, next_run: null, created_at: new Date().toISOString() },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: { task_type: string; target_id: string; target_name: string; interval_seconds: number }) => {
    try {
      await taskApi.createTask(values)
      message.success('任务创建成功')
      setModalOpen(false)
      form.resetFields()
      fetchTasks()
    } catch {
      message.error('创建失败')
    }
  }

  const handleRun = async (taskId: number) => {
    try {
      await taskApi.runTask(taskId)
      message.success('任务已启动')
    } catch {
      message.error('启动失败')
    }
  }

  const handleDelete = async (taskId: number) => {
    try {
      await taskApi.deleteTask(taskId)
      message.success('任务已删除')
      fetchTasks()
    } catch {
      message.error('删除失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    {
      title: '类型',
      dataIndex: 'task_type',
      render: (type: string) => (
        <Tag color={type === 'user' ? 'blue' : type === 'video' ? 'green' : 'orange'}>{type}</Tag>
      ),
    },
    { title: '目标', dataIndex: 'target_name' },
    { title: '间隔', dataIndex: 'interval_seconds', render: (v: number) => `${v / 60} 分钟` },
    {
      title: '状态',
      dataIndex: 'is_active',
      render: (active: boolean) => <Tag color={active ? 'success' : 'default'}>{active ? '运行中' : '已停止'}</Tag>,
    },
    { title: '上次执行', dataIndex: 'last_run', render: (v: string) => v ? formatDate(v) : '-' },
    {
      title: '操作',
      render: (_: unknown, record: Task) => (
        <Space>
          <Button size="small" icon={<PlayCircleOutlined />} onClick={() => handleRun(record.id)}>执行</Button>
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>监控中心</h2>

      <Card
        bordered={false}
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>新建任务</Button>}
      >
        <Table columns={columns} dataSource={tasks} rowKey="id" loading={loading} />
      </Card>

      <Modal title="新建监控任务" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="task_type" label="任务类型" rules={[{ required: true }]}>
            <Select options={[{ value: 'user', label: '用户监控' }, { value: 'video', label: '视频监控' }, { value: 'live', label: '直播监控' }]} />
          </Form.Item>
          <Form.Item name="target_id" label="目标ID" rules={[{ required: true }]}>
            <Input placeholder="sec_uid 或 aweme_id" />
          </Form.Item>
          <Form.Item name="target_name" label="目标名称">
            <Input placeholder="便于识别的名称" />
          </Form.Item>
          <Form.Item name="interval_seconds" label="监控间隔(秒)" initialValue={3600}>
            <InputNumber min={60} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TaskCenter
