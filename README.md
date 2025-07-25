# 🐟 XianYuAutoDeliveryX - 闲鱼虚拟商品商自动发货&聊天对接大模型

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**✨ 基于闲鱼API的自动发货系统，支持虚拟商品商品聊天窗口自动发货、消息自动回复等功能。**
**⚠️ 注意：本项目仅供学习交流使用，请勿用于商业用途。**

## 🌟 核心特性

- 🔐 **用户认证系统** - 安全的登录认证，保护管理界面
- 👥 **多账号管理** - 支持同时管理多个闲鱼账号
- 🎯 **智能关键词回复** - 每个账号独立的关键词回复设置
- 💾 **数据持久化** - SQLite数据库存储账号和关键词数据
- 🌐 **美观Web界面** - 响应式设计，操作简单直观
- 📡 **API接口** - 完整的RESTful API支持
- 🔄 **实时消息处理** - 基于WebSocket的实时消息监控
- 📊 **订单状态监控** - 实时跟踪订单状态变化
- 📝 **完善的日志系统** - 详细的操作日志记录

## 🛠️ 快速开始

### ⛳ 运行环境
- Python 3.7+

### 🎯 安装依赖
```bash
pip install -r requirements.txt
```

### 🎨 配置说明
1. 在 `global_config.yml` 中配置基本参数
2. 系统支持多账号管理，可通过Web界面添加多个闲鱼账号Cookie

### 🚀 运行项目
```bash
python Start.py
```

### 🔐 登录系统
1. 启动后访问 `http://localhost:8080`
2. 默认登录账号：
   - 用户名：`admin`
   - 密码：`admin123`
3. 登录后可进入管理界面进行操作

## 📁 项目结构
```
├── Start.py              # 项目启动入口
├── XianyuAutoAsync.py    # 核心业务逻辑
├── config.py             # 配置管理
├── cookie_manager.py     # Cookie管理器
├── db_manager.py         # 数据库管理
├── reply_server.py       # FastAPI服务器
├── utils/                # 工具函数目录
│   ├── xianyu_utils.py   # 闲鱼相关工具
│   ├── message_utils.py  # 消息处理工具
│   └── ws_utils.py       # WebSocket工具
├── static/               # 静态资源
│   ├── index.html        # 管理界面
│   └── login.html        # 登录页面
├── logs/                 # 日志文件
├── global_config.yml     # 全局配置文件
├── xianyu_data.db        # SQLite数据库
└── requirements.txt      # Python依赖
```

## 🎯 主要功能

### 1. 用户认证系统
- 安全的登录认证机制
- Session token管理
- 自动登录状态检查
- 登出功能

### 2. 多账号管理
- 支持添加多个闲鱼账号
- 每个账号独立管理
- Cookie安全存储
- 账号状态监控

### 3. 智能关键词回复
- 每个账号独立的关键词设置
- 支持变量替换：`{send_user_name}`, `{send_user_id}`, `{send_message}`
- 实时关键词匹配
- 默认回复机制

### 4. Web管理界面
- 响应式设计，支持移动端
- 直观的操作界面
- 实时数据更新
- 操作反馈提示

## 🔌 API 接口说明

### 智能回复接口
`POST http://localhost:8080/xianyu/reply`

#### 接口说明
你需要实现这个接口，本项目会调用这个接口获取自动回复的内容并发送给客户
不实现这个接口也没关系，系统会默认回复，你也可以配置默认回复的内容
用于处理闲鱼消息的自动回复，支持对接大语言模型进行智能回复。

**通过这个接口可以检测到用户是否已付款，然后回复虚拟资料内容即可**
#### 请求参数
```json
{
    "msg_time": "消息时间",
    "user_url": "用户主页URL",
    "send_user_id": "发送者ID",
    "send_user_name": "发送者昵称",
    "item_id": "商品ID",
    "send_message": "发送的消息内容",
    "chat_id": "会话ID"
}
```

#### 响应格式
```json
{
    "code": 200,
    "data": {
        "send_msg": "回复的消息内容"
    }
}
```

#### 配置示例
```yaml
AUTO_REPLY:
  api:
    enabled: true  # 是否启用API回复
    timeout: 10    # 超时时间（秒）
    url: http://localhost:8080/xianyu/reply
```

#### 使用场景
- 当收到买家消息时，系统会自动调用此接口
- 支持接入 ChatGPT、文心一言等大语言模型
- 支持自定义回复规则和模板
- 支持消息变量替换（如 `{send_user_name}`）

#### 注意事项
- 接口需要返回正确的状态码（200）和消息内容
- 建议实现错误重试机制
- 注意处理超时情况（默认10秒）
- 可以根据需要扩展更多的参数和功能

## 🗝️ 注意事项
- 请确保闲鱼账号已登录并获取有效的 Cookie
- 建议在正式环境使用前先在测试环境验证
- 定期检查日志文件，及时处理异常情况
- 使用大模型时注意 API 调用频率和成本控制

## 📝 效果


![image-20250611004531745](https://typeropic.oss-cn-beijing.aliyuncs.com/cp/image-20250611004531745.png)

![image-20250611004549662](https://typeropic.oss-cn-beijing.aliyuncs.com/cp/image-20250611004549662.png)

## 🧸特别鸣谢

本项目参考了以下开源项目： https://github.com/cv-cat/XianYuApis

感谢[@CVcat](https://github.com/cv-cat)的技术支持

## 📞 联系方式
如有问题或建议，欢迎提交 Issue 或 Pull Request。

## 技术交流

![image-20250611004141387](https://typeropic.oss-cn-beijing.aliyuncs.com/cp/image-20250611004141387.png)
