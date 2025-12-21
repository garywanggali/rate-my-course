# 课程评价平台

一个基于 Django 和 SQLite 的课程评价平台，允许学生评价和讨论课程。

## 功能特性

### 核心功能
- **用户系统**: 注册、登录、用户个人主页
- **课程评价**: 多维度评分系统（总体、难度、实用性、作业量）
- **评论系统**: 支持多级回复的评论功能
- **标签系统**: 用户可以为课程添加标签
- **搜索与筛选**: 按课程名、学校、院系、标签等筛选
- **排行榜**: 显示热门课程 Top 10
- **收藏功能**: 用户可以收藏感兴趣的课程
- **教师主页**: 查看教师授课的课程和平均评分

### 交互功能
- **评价反应**: 对评价点"有帮助"或"无帮助"
- **匿名评价**: 用户可以选择匿名发布评价
- **举报系统**: 可以举报不当内容
- **多级评论**: 支持评论的回复和嵌套回复

## 技术栈

- **后端**: Django
- **数据库**: SQLite (Django ORM)
- **认证**: Django Auth
- **前端**: HTML, CSS, JavaScript (原生)

## 安装与运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 迁移数据库

```bash
python manage.py migrate
```

### 3. 运行应用

```bash
python manage.py runserver 8000
```

应用将在 `http://localhost:8000` 启动。

## 测试账号

可使用 Django Admin 创建测试账号，或在注册页自行注册。

## 数据库结构

### 主要表
- `user`: 用户信息
- `school`: 学校信息
- `course`: 课程信息
- `instructor`: 教师信息
- `rating`: 评价信息
- `comment`: 评论信息
- `tag`: 标签信息
- `course_tag`: 课程标签关联
- `rating_reaction`: 评价反应
- `report`: 举报信息
- `favorite`: 收藏信息

## 项目结构

```
rate_my_course/
├── manage.py             # Django 管理入口
├── rate_my_course/       # Django 项目
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                 # 应用
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── requirements.txt      # Python 依赖
├── templates/            # HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── courses.html
│   ├── course_detail.html
│   ├── user_profile.html
│   ├── instructor_profile.html
│   ├── rankings.html
│   └── comment_item.html
└── static/               # 静态文件
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## 主要路由

- `/`: 首页，显示热门课程和最新评价
- `/register`: 用户注册
- `/login`: 用户登录
- `/logout`: 用户退出
- `/courses`: 课程列表（支持搜索和筛选）
- `/course/<id>`: 课程详情页
- `/course/<id>/rate`: 评价课程
- `/user/<id>`: 用户个人主页
- `/instructor/<id>`: 教师主页
- `/rankings`: 课程排行榜

## 开发说明

### 添加新功能

1. 在 `core/models.py` 中添加新的数据库模型
2. 在 `core/views.py` 与 `core/urls.py` 中添加新的视图与路由
3. 在 `templates/` 中创建或修改 HTML 模板
4. 在 `static/css/style.css` 中添加样式（如需要）
5. 在 `static/js/main.js` 中添加 JavaScript 功能（如需要）

### 数据库迁移

当前使用 SQLite 数据库，文件为 `rate_my_course.db`。如需迁移到其他数据库，修改 `rate_my_course/settings.py` 中的数据库配置。

## 注意事项

- 生产环境请修改 `SECRET_KEY`
- 建议配置 `ALLOWED_HOSTS`
- 可以添加更多验证和错误处理
- 使用 Django Admin 进行基础管理

## 许可证

MIT License
