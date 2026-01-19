# 抖音数据分析平台

基于 FastAPI 和 React 的抖音数据分析平台，提供数据采集、实时监控、深度分析等功能。

## 功能特性

### 数据采集
- 用户资料采集（粉丝数、作品数、获赞数等）
- 视频数据采集（播放量、点赞、评论、分享等）
- 评论数据采集（支持评论回复）
- 直播数据采集（实时弹幕、在线人数）

### 数据监控
- 用户粉丝变化监控
- 视频数据变化追踪
- 定时任务调度
- 数据快照存储

### 数据分析
- 用户深度分析（互动率、发布频率等）
- 视频数据分析（传播指数、参与度等）
- 评论情感分析
- 趋势分析

### 热榜监控
- 热搜榜实时获取
- 视频热榜
- 直播热榜

## 技术栈

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL / SQLite
- **缓存**: Redis
- **任务调度**: APScheduler

### 前端
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design 5
- **状态管理**: Zustand
- **图表**: ECharts

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (可选，默认使用 SQLite)
- Redis 7+ (可选)

### 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env

# 编辑 .env 文件，设置你的抖音 Cookie
# DOUYIN_COOKIE="你的cookie"

# 启动服务
python run.py
```

服务启动后访问:
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

### Docker 启动

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d
```

## API 概览

### 用户相关 (10个接口)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/users/profile/{sec_uid} | 获取用户资料 |
| GET | /api/users/posts/{sec_uid} | 获取用户作品 |
| GET | /api/users/likes/{sec_uid} | 获取用户喜欢 |
| GET | /api/users/following/{sec_uid} | 获取关注列表 |
| GET | /api/users/followers/{sec_uid} | 获取粉丝列表 |
| GET | /api/users/mixes/{sec_uid} | 获取用户合集 |
| GET | /api/users/history/{user_id} | 获取粉丝历史 |
| POST | /api/users/compare | 用户对比分析 |
| POST | /api/users/batch | 批量获取用户 |

### 视频相关 (8个接口)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/videos/detail/{aweme_id} | 获取视频详情 |
| GET | /api/videos/comments/{aweme_id} | 获取视频评论 |
| GET | /api/videos/replies/{comment_id} | 获取评论回复 |
| GET | /api/videos/related/{aweme_id} | 获取相关推荐 |
| GET | /api/videos/mix/{mix_id} | 获取合集视频 |
| GET | /api/videos/history/{video_id} | 获取数据历史 |
| POST | /api/videos/parse | 解析视频链接 |
| POST | /api/videos/download | 下载视频 |

### 直播相关 (6个接口)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/lives/info/{room_id} | 获取直播间信息 |
| GET | /api/lives/by-user/{sec_uid} | 通过用户获取直播 |
| GET | /api/lives/danmaku/{room_id} | 获取历史弹幕 |
| GET | /api/lives/ranking | 直播热门榜 |
| WS | /api/ws/live/{room_id} | 实时弹幕WebSocket |
| POST | /api/lives/record | 开始录制 |

### 搜索相关 (5个接口)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/search/video | 搜索视频 |
| GET | /api/search/user | 搜索用户 |
| GET | /api/search/live | 搜索直播 |
| GET | /api/search/suggest | 搜索建议 |
| GET | /api/search/trending | 热门搜索词 |

### 热榜相关 (4个接口)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/ranking/boards | 获取榜单列表 |
| GET | /api/ranking/hot/{board_type} | 获取热搜榜 |
| GET | /api/ranking/video | 视频榜 |
| GET | /api/ranking/live | 直播榜 |

### 任务管理 (6个接口)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/tasks | 获取任务列表 |
| POST | /api/tasks | 创建任务 |
| PUT | /api/tasks/{task_id} | 更新任务 |
| DELETE | /api/tasks/{task_id} | 删除任务 |
| POST | /api/tasks/{task_id}/run | 立即执行 |
| GET | /api/tasks/{task_id}/logs | 获取日志 |

### 分析相关 (5个接口)
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/analysis/user | 用户深度分析 |
| POST | /api/analysis/video | 视频数据分析 |
| POST | /api/analysis/comments | 评论情感分析 |
| POST | /api/analysis/trends | 趋势分析 |
| GET | /api/analysis/report/{id} | 获取分析报告 |

## 项目结构

```
douyin-analytics-platform/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── core/              # 核心模块 (爬虫、签名)
│   │   ├── services/          # 业务服务层
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic 模式
│   │   ├── db/                # 数据库连接
│   │   ├── cache/             # 缓存层
│   │   └── utils/             # 工具函数
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # 前端应用
├── docker-compose.yml
└── README.md
```

## 注意事项

1. **Cookie 配置**: 需要在 `.env` 文件中配置有效的抖音 Cookie 才能正常使用 API
2. **速率限制**: 请合理控制请求频率，避免被封禁
3. **数据安全**: 请勿将敏感数据（如 Cookie）提交到版本控制

## 开发计划

- [x] 后端 API 开发
- [x] 数据库设计
- [x] 爬虫引擎
- [ ] 前端界面开发
- [ ] 定时任务系统
- [ ] 数据可视化
- [ ] 告警通知

## 许可证

MIT License
