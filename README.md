# 🚀 闲鱼自动回复管理系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)
![Docker](https://img.shields.io/badge/Docker-支持-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/Version-v2.0.0-brightgreen.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)

**一个功能强大的闲鱼自动回复管理系统，支持多账号管理、AI智能回复、自动发货等功能**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [部署方式](#-部署方式) • [使用文档](#-使用文档) • [API文档](#-api文档) • [贡献指南](#-贡献指南)

</div>

## 📋 项目概述

闲鱼自动回复管理系统是一个基于 Python + FastAPI 开发的自动化客服系统，专为闲鱼平台设计。系统通过 WebSocket 连接闲鱼服务器，实时接收和处理消息，提供智能化的自动回复服务。

### 🎯 核心优势

- **🤖 AI智能回复**：集成多种AI模型，支持意图识别和智能议价
- **🔄 多账号管理**：同时管理多个闲鱼账号，独立配置和监控
- **📦 商品管理**：自动收集和管理商品信息，支持批量操作
- **🚚 自动发货**：智能匹配发货规则，自动发送卡券信息
- **📊 实时监控**：完整的日志系统和状态监控
- **🐳 容器化部署**：支持Docker一键部署，简化运维

## ✨ 功能特性

### 🤖 AI智能回复
- **多模型支持**：支持通义千问、GPT等主流AI模型
- **意图识别**：自动识别价格咨询、技术问题、通用咨询
- **智能议价**：阶梯式降价策略，可设置最大优惠幅度
- **上下文感知**：记住完整对话历史，提供连贯回复
- **自定义提示词**：支持针对不同场景自定义AI提示词

### 👥 多账号管理
- **账号隔离**：每个账号独立配置和管理
- **批量操作**：支持批量添加、删除、配置账号
- **状态监控**：实时监控账号连接状态和消息处理情况
- **权限控制**：基于JWT的安全认证系统

### 📦 商品管理
- **自动收集**：消息触发时自动收集商品信息
- **详情获取**：通过API获取完整商品详情
- **批量管理**：支持查看、编辑、删除商品信息
- **智能匹配**：基于商品信息进行关键词匹配

### 🚚 自动发货
- **规则配置**：灵活的发货规则配置系统
- **卡券管理**：支持多种卡券类型和批量导入
- **智能匹配**：根据商品信息自动匹配发货规则
- **发货记录**：完整的发货历史记录和统计

### 📊 监控与日志
- **实时日志**：多级别日志记录和实时查看
- **性能监控**：系统资源使用情况监控
- **消息统计**：消息处理统计和分析
- **健康检查**：完整的系统健康检查机制

## 🛠️ 技术栈

### 后端技术
- **Python 3.11+**：主要开发语言
- **FastAPI**：现代化的Web框架
- **SQLite**：轻量级数据库
- **WebSocket**：实时通信
- **AsyncIO**：异步编程

### 前端技术
- **HTML5 + CSS3**：现代化界面设计
- **JavaScript (ES6+)**：交互逻辑
- **Bootstrap**：响应式布局
- **Chart.js**：数据可视化

### 部署技术
- **Docker**：容器化部署
- **Docker Compose**：多容器编排
- **Nginx**：反向代理和负载均衡
- **SSL/TLS**：安全传输

## 🚀 快速开始

> 💡 **推荐使用Docker镜像部署，无需配置环境，一键启动！**

### 🐳 方式一：Docker 镜像部署（推荐）

**使用预构建的Docker镜像，一键启动：**

```bash
docker run -d -p 8080:8080 --name xianyu-auto-reply --privileged=true registry.cn-shanghai.aliyuncs.com/zhinian-software/xianyu-auto-reply:1.0
```

**特点：**
- ✅ **零配置**：无需安装Python环境和依赖
- ✅ **即开即用**：一条命令启动完整系统
- ✅ **稳定可靠**：经过测试的稳定版本
- ✅ **自动更新**：支持数据持久化和版本升级

**访问系统：**
- 🌐 Web界面：http://localhost:8080
- 👤 默认账号：admin / admin123
- 📖 API文档：http://localhost:8080/docs

**常用管理命令：**
```bash
# 查看容器状态
docker ps

# 查看容器日志
docker logs xianyu-auto-reply

# 重启容器
docker restart xianyu-auto-reply

# 停止容器
docker stop xianyu-auto-reply

# 删除容器
docker rm xianyu-auto-reply
```

### 方式二：Docker 源码部署

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/xianyu-auto-reply.git
   cd xianyu-auto-reply
   ```

2. **一键部署**
   ```bash
   ./deploy.sh
   ```

3. **访问系统**
   - 打开浏览器访问：http://localhost:8080
   - 默认账号：admin / admin123

### 方式三：本地部署

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **启动系统**
   ```bash
   python Start.py
   ```

3. **访问系统**
   - 打开浏览器访问：http://localhost:8080

## 📚 使用文档

### 基础使用
1. **[使用说明](./使用说明.md)** - 系统基础使用指南
2. **[Docker部署说明](./Docker部署说明.md)** - Docker部署详细说明

### 功能文档
1. **[AI回复功能指南](./AI_REPLY_GUIDE.md)** - AI回复功能详细说明
2. **[商品管理功能说明](./商品管理功能说明.md)** - 商品管理功能使用
3. **[自动发货功能说明](./自动发货功能说明.md)** - 自动发货配置和使用
4. **[日志管理功能说明](./日志管理功能说明.md)** - 日志查看和管理
5. **[获取所有商品功能说明](./获取所有商品功能说明.md)** - 商品批量获取功能

## 🔧 配置说明

### 环境变量配置
```bash
# 基础配置
TZ=Asia/Shanghai
WEB_PORT=8080

# 管理员账号
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# AI回复配置
AI_REPLY_ENABLED=true
DEFAULT_AI_MODEL=qwen-plus
DEFAULT_AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 全局配置文件
主要配置文件为 `global_config.yml`，包含：
- API端点配置
- WebSocket连接配置
- 自动回复配置
- 日志配置
- 商品详情获取配置

## 📡 API文档

### 认证接口
- `POST /login` - 用户登录
- `POST /logout` - 用户登出

### 账号管理
- `GET /cookies` - 获取所有账号
- `POST /cookies` - 添加新账号
- `DELETE /cookies/{cookie_id}` - 删除账号

### AI回复管理
- `GET /ai-reply/{cookie_id}` - 获取AI配置
- `POST /ai-reply/{cookie_id}` - 保存AI配置
- `POST /ai-reply/{cookie_id}/test` - 测试AI回复

### 商品管理
- `GET /items` - 获取所有商品
- `GET /items/cookie/{cookie_id}` - 获取指定账号商品
- `PUT /items/{cookie_id}/{item_id}` - 更新商品详情

### 系统监控
- `GET /health` - 健康检查
- `GET /logs` - 获取系统日志
- `GET /logs/stats` - 日志统计信息

完整API文档访问：http://localhost:8080/docs

## 🏗️ 项目结构

```
xianyu-auto-reply/
├── Start.py                    # 项目启动入口
├── XianyuAutoAsync.py         # 闲鱼WebSocket客户端
├── reply_server.py            # FastAPI Web服务器
├── config.py                  # 配置管理
├── cookie_manager.py          # Cookie账号管理
├── db_manager.py              # 数据库管理
├── ai_reply_engine.py         # AI回复引擎
├── file_log_collector.py      # 文件日志收集器
├── bargain_demo.py            # 议价功能演示
├── global_config.yml          # 全局配置文件
├── requirements.txt           # Python依赖
├── Dockerfile                 # Docker镜像构建
├── docker-compose.yml         # Docker编排配置
├── deploy.sh                  # 部署脚本
├── static/                    # 前端静态文件
│   ├── index.html            # 主页面
│   ├── login.html            # 登录页面
│   └── xianyu_js_version_2.js # 前端逻辑
├── utils/                     # 工具模块
│   ├── xianyu_utils.py       # 闲鱼工具函数
│   ├── message_utils.py      # 消息处理工具
│   └── ws_utils.py           # WebSocket工具
├── nginx/                     # Nginx配置
├── docs/                      # 文档目录
└── backups/                   # 备份目录
```

## 🤝 贡献指南

我们欢迎任何形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献指南。

### 快速开始贡献
1. **Fork** 项目到你的GitHub账号
2. **克隆**项目到本地开发环境
3. **创建分支**进行功能开发或问题修复
4. **提交代码**并创建Pull Request

### 贡献类型
- 🐛 **问题报告**：发现bug或提出改进建议
- 💡 **功能建议**：提出新功能想法
- 🔧 **代码贡献**：修复问题或开发新功能
- 📚 **文档改进**：完善文档和说明
- 🧪 **测试用例**：添加或改进测试

详细信息请参考：[贡献指南](CONTRIBUTING.md)

## 💬 社区交流

### 加入我们的交流群

<div align="center">

| 微信交流群 | QQ交流群 |
|:---:|:---:|
| <img src="https://img.zhinianboke.com/img/5527" width="200" alt="微信群二维码"> | <img src="https://img.zhinianboke.com/img/5526" width="200" alt="QQ群二维码"> |
| 扫码加入微信群 | 扫码加入QQ群 |

</div>

### 交流内容
- 💡 **功能讨论**：新功能建议和讨论
- 🐛 **问题求助**：使用过程中遇到的问题
- 📚 **经验分享**：使用技巧和最佳实践
- 🔄 **版本更新**：最新版本发布通知
- 🤝 **合作交流**：开发合作和技术交流

### 群规说明
- 请保持友善和尊重的交流氛围
- 优先使用搜索功能查找已有答案
- 提问时请提供详细的问题描述和环境信息
- 欢迎分享使用经验和改进建议

## 📄 许可证

本项目采用 MIT 许可证，详情请查看 [LICENSE](LICENSE) 文件。

## 📋 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解详细的版本更新历史。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

### 特别感谢
- 所有提交代码的贡献者
- 提供问题反馈的用户
- 完善文档的志愿者
- 推广项目的支持者

### 技术支持
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Web框架
- [SQLite](https://www.sqlite.org/) - 轻量级数据库
- [Docker](https://www.docker.com/) - 容器化技术
- [Loguru](https://github.com/Delgan/loguru) - 优秀的日志库

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！**

[📋 报告问题](https://github.com/your-repo/xianyu-auto-reply/issues) • [💡 功能建议](https://github.com/your-repo/xianyu-auto-reply/issues) • [🤝 参与贡献](https://github.com/your-repo/xianyu-auto-reply/pulls) • [📖 查看文档](https://github.com/your-repo/xianyu-auto-reply/wiki)

**让我们一起构建更好的闲鱼自动化工具！** 🚀

</div>

## 🔧 核心模块说明

### Start.py - 项目启动入口
- 初始化文件日志收集器
- 创建和管理 CookieManager
- 启动 FastAPI Web服务器
- 加载配置文件和环境变量中的账号

### XianyuAutoAsync.py - 闲鱼WebSocket客户端
- 维持与闲鱼服务器的WebSocket连接
- 处理消息接收和发送
- 自动刷新token和维持心跳
- 商品信息获取和处理
- 自动回复逻辑处理

### reply_server.py - FastAPI Web服务器
- 提供Web管理界面
- RESTful API接口
- 用户认证和权限控制
- 文件上传和下载
- 健康检查和监控

### ai_reply_engine.py - AI回复引擎
- 多AI模型支持（通义千问、GPT等）
- 意图识别和分类
- 智能议价逻辑
- 对话历史管理
- 自定义提示词处理

### db_manager.py - 数据库管理
- SQLite数据库操作
- 数据表结构管理
- 数据备份和恢复
- 事务处理和连接池

## 🎮 使用场景

### 个人卖家
- **自动客服**：24小时自动回复买家咨询
- **智能议价**：自动处理价格谈判，提高成交率
- **快速发货**：自动发送卡券和虚拟商品

### 商家店铺
- **多账号管理**：统一管理多个闲鱼账号
- **批量操作**：批量设置关键词和回复规则
- **数据分析**：查看消息统计和销售数据

### 代运营服务
- **客户隔离**：为不同客户提供独立的账号管理
- **定制化配置**：根据客户需求定制回复策略
- **监控报告**：提供详细的运营数据报告

## 🔒 安全特性

### 数据安全
- **本地存储**：所有数据存储在本地，不上传到第三方
- **加密传输**：支持HTTPS和WSS加密传输
- **权限控制**：基于JWT的用户认证系统

### 隐私保护
- **Cookie加密**：敏感信息加密存储
- **日志脱敏**：自动过滤敏感信息
- **访问控制**：IP白名单和访问频率限制

## 📈 性能优化

### 系统性能
- **异步处理**：全异步架构，高并发处理能力
- **连接池**：数据库连接池，提高数据库操作效率
- **缓存机制**：智能缓存，减少重复请求

### 资源优化
- **内存管理**：自动清理过期数据和缓存
- **日志轮转**：自动清理过期日志文件
- **资源限制**：Docker资源限制，防止资源滥用

## 🚨 故障排除

### 常见问题

**Q: 系统启动失败？**
A: 检查以下项目：
- Python版本是否为3.11+
- 依赖包是否正确安装
- 端口8080是否被占用
- 配置文件是否存在

**Q: WebSocket连接失败？**
A: 检查以下方面：
- 网络连接是否正常
- Cookie是否有效
- 防火墙设置
- 代理配置

**Q: AI回复不工作？**
A: 检查以下配置：
- AI API密钥是否正确
- API地址是否可访问
- 账户余额是否充足
- 网络连接是否稳定

### 日志查看
```bash
# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs xianyu-app

# 查看系统日志文件
tail -f logs/xianyu_$(date +%Y-%m-%d).log
```

## 🤝 贡献指南

我们欢迎任何形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献指南。

### 快速开始贡献
1. **Fork** 项目到你的GitHub账号
2. **克隆**项目到本地开发环境
3. **创建分支**进行功能开发或问题修复
4. **提交代码**并创建Pull Request

### 贡献类型
- 🐛 **问题报告**：发现bug或提出改进建议
- 💡 **功能建议**：提出新功能想法
- 🔧 **代码贡献**：修复问题或开发新功能
- 📚 **文档改进**：完善文档和说明
- 🧪 **测试用例**：添加或改进测试

### 开发规范
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 代码风格
- 使用 [Conventional Commits](https://www.conventionalcommits.org/) 提交规范
- 为新功能添加相应的测试用例
- 更新相关文档和说明

详细信息请参考：[贡献指南](CONTRIBUTING.md)

## 📄 许可证

本项目采用 MIT 许可证，详情请查看 [LICENSE](LICENSE) 文件。

## � 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解详细的版本更新历史。

## �🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

### 特别感谢
- 所有提交代码的贡献者
- 提供问题反馈的用户
- 完善文档的志愿者
- 推广项目的支持者

### 技术支持
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Web框架
- [SQLite](https://www.sqlite.org/) - 轻量级数据库
- [Docker](https://www.docker.com/) - 容器化技术
- [Loguru](https://github.com/Delgan/loguru) - 优秀的日志库

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！**

[📋 报告问题](https://github.com/your-repo/xianyu-auto-reply/issues) • [💡 功能建议](https://github.com/your-repo/xianyu-auto-reply/issues) • [🤝 参与贡献](https://github.com/your-repo/xianyu-auto-reply/pulls) • [📖 查看文档](https://github.com/your-repo/xianyu-auto-reply/wiki)

**让我们一起构建更好的闲鱼自动化工具！** 🚀

</div>
