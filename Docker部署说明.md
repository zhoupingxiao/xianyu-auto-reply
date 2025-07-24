# 🐳 Docker 部署说明

## 📋 部署概述

本项目支持完整的Docker容器化部署，包含所有必要的依赖和配置。支持单容器部署和多容器编排部署。

## 🚀 快速开始

### 方式一：使用 Docker Compose（推荐）

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd xianyuapis
   ```

2. **配置环境变量**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑配置文件（可选）
   nano .env
   ```

3. **启动服务**
   ```bash
   # 启动基础服务
   docker-compose up -d
   
   # 或者启动包含Nginx的完整服务
   docker-compose --profile with-nginx up -d
   ```

4. **访问系统**
   - 基础部署：http://localhost:8080
   - 带Nginx：http://localhost

### 方式二：使用 Docker 命令

1. **构建镜像**
   ```bash
   docker build -t xianyu-auto-reply:latest .
   ```

2. **运行容器**
   ```bash
   docker run -d \
     --name xianyu-auto-reply \
     -p 8080:8080 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/global_config.yml:/app/global_config.yml:ro \
     -e ADMIN_USERNAME=admin \
     -e ADMIN_PASSWORD=admin123 \
     xianyu-auto-reply:latest
   ```

## 📦 依赖说明

### 新增依赖
- `python-multipart>=0.0.6` - 文件上传支持（商品管理功能需要）

### 完整依赖列表
```
# Web框架和API相关
fastapi>=0.111
uvicorn[standard]>=0.29
pydantic>=2.7
python-multipart>=0.0.6

# 日志记录
loguru>=0.7

# 网络通信
websockets>=10.0,<13.0
aiohttp>=3.9

# 配置文件处理
PyYAML>=6.0

# JavaScript执行引擎
PyExecJS>=1.5.1

# 协议缓冲区解析
blackboxprotobuf>=1.0.1

# 系统监控
psutil>=5.9.0

# HTTP客户端（用于测试）
requests>=2.31.0
```

## 🔧 配置说明

### 环境变量配置

#### 基础配置
```bash
# 时区设置
TZ=Asia/Shanghai

# 服务端口
WEB_PORT=8080

# 管理员账号（建议修改）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# JWT密钥（建议修改）
JWT_SECRET_KEY=your-secret-key-here
```

#### 功能配置
```bash
# 自动回复
AUTO_REPLY_ENABLED=true

# 自动发货
AUTO_DELIVERY_ENABLED=true
AUTO_DELIVERY_TIMEOUT=30

# 商品管理（新功能）
ENABLE_ITEM_MANAGEMENT=true
```

### 数据持久化

#### 重要目录
- `/app/data` - 数据库文件
- `/app/logs` - 日志文件
- `/app/backups` - 备份文件

#### 挂载配置
```yaml
volumes:
  - ./data:/app/data:rw          # 数据库持久化
  - ./logs:/app/logs:rw          # 日志持久化
  - ./backups:/app/backups:rw    # 备份持久化
  - ./global_config.yml:/app/global_config.yml:ro  # 配置文件
```

## 🏗️ 架构说明

### 容器架构
```
┌─────────────────────────────────────┐
│           Nginx (可选)              │
│         反向代理 + SSL              │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│        Xianyu App Container         │
│  ┌─────────────────────────────────┐ │
│  │        FastAPI Server          │ │
│  │         (Port 8080)            │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │      XianyuAutoAsync           │ │
│  │     (WebSocket Client)         │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │       SQLite Database          │ │
│  │      (商品信息 + 配置)          │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 新功能支持
- ✅ 商品信息管理
- ✅ 商品详情编辑
- ✅ 文件上传功能
- ✅ 消息通知格式化

## 🔍 健康检查

### 内置健康检查
```bash
# 检查容器状态
docker ps

# 查看健康状态
docker inspect xianyu-auto-reply | grep Health -A 10

# 手动健康检查
curl -f http://localhost:8080/health
```

### 健康检查端点
- `GET /health` - 基础健康检查
- `GET /api/status` - 详细状态信息

## 📊 监控和日志

### 日志查看
```bash
# 查看容器日志
docker logs xianyu-auto-reply

# 实时查看日志
docker logs -f xianyu-auto-reply

# 查看应用日志文件
docker exec xianyu-auto-reply tail -f /app/logs/xianyu_$(date +%Y%m%d).log
```

### 性能监控
```bash
# 查看资源使用
docker stats xianyu-auto-reply

# 进入容器
docker exec -it xianyu-auto-reply bash

# 查看进程状态
docker exec xianyu-auto-reply ps aux
```

## 🔒 安全配置

### 生产环境建议
1. **修改默认密码**
   ```bash
   ADMIN_USERNAME=your-admin
   ADMIN_PASSWORD=your-strong-password
   ```

2. **使用强JWT密钥**
   ```bash
   JWT_SECRET_KEY=$(openssl rand -base64 32)
   ```

3. **启用HTTPS**
   ```yaml
   # 使用Nginx配置SSL
   docker-compose --profile with-nginx up -d
   ```

4. **限制网络访问**
   ```yaml
   # 仅允许本地访问
   ports:
     - "127.0.0.1:8080:8080"
   ```

## 🚨 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看详细错误
   docker logs xianyu-auto-reply
   
   # 检查端口占用
   netstat -tlnp | grep 8080
   ```

2. **数据库初始化失败**
   ```bash
   # 数据库会在应用启动时自动初始化
   # 如果需要重新初始化，可以删除数据库文件后重启容器
   docker exec xianyu-auto-reply rm -f /app/data/xianyu_data.db
   docker restart xianyu-auto-reply
   ```

3. **权限问题**
   ```bash
   # 修复目录权限
   sudo chown -R 1000:1000 ./data ./logs ./backups
   ```

4. **依赖安装失败**
   ```bash
   # 重新构建镜像
   docker-compose build --no-cache
   ```

### 调试模式
```bash
# 启用调试模式
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up -d

# 或设置环境变量
docker run -e DEBUG=true -e LOG_LEVEL=DEBUG ...
```

## 🔄 更新部署

### 更新步骤
1. **停止服务**
   ```bash
   docker-compose down
   ```

2. **拉取最新代码**
   ```bash
   git pull origin main
   ```

3. **重新构建**
   ```bash
   docker-compose build --no-cache
   ```

4. **启动服务**
   ```bash
   docker-compose up -d
   ```

### 数据备份
```bash
# 备份数据库
docker exec xianyu-auto-reply cp /app/data/xianyu_data.db /app/backups/

# 备份配置
cp .env .env.backup
cp global_config.yml global_config.yml.backup
```

## 📈 性能优化

### 资源限制
```yaml
deploy:
  resources:
    limits:
      memory: 512M      # 内存限制
      cpus: '0.5'       # CPU限制
    reservations:
      memory: 256M      # 内存预留
      cpus: '0.25'      # CPU预留
```

### 优化建议
1. **调整内存限制**：根据实际使用情况调整
2. **使用SSD存储**：提高数据库性能
3. **配置日志轮转**：避免日志文件过大
4. **定期清理**：清理旧的备份文件

---

🎉 **Docker部署配置完善，支持所有新功能！**
