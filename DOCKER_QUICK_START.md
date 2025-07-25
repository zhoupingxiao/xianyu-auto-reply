# Docker快速部署指南 - 多用户版本

## 🚀 一键部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd xianyu-auto-reply
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件（重要！）
nano .env
```

**必须修改的配置**：
```bash
# 修改管理员密码
ADMIN_PASSWORD=your-secure-password

# 修改JWT密钥
JWT_SECRET_KEY=your-very-long-and-random-secret-key

# 多用户功能配置
MULTIUSER_ENABLED=true
USER_REGISTRATION_ENABLED=true
EMAIL_VERIFICATION_ENABLED=true
CAPTCHA_ENABLED=true
```

### 3. 启动服务
```bash
# 构建并启动
docker-compose up -d --build

# 查看启动状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 验证部署
```bash
# 健康检查
curl http://localhost:8080/health

# 访问注册页面
curl http://localhost:8080/register.html
```

## 🎯 快速测试

### 访问地址
- **主页**: http://localhost:8080
- **登录页面**: http://localhost:8080/login.html
- **注册页面**: http://localhost:8080/register.html

### 默认管理员账号
- **用户名**: admin
- **密码**: admin123（请立即修改）

### 测试多用户功能
1. 访问注册页面
2. 输入用户信息
3. 验证图形验证码
4. 接收邮箱验证码
5. 完成注册
6. 登录测试数据隔离

## 🔧 常用命令

### 服务管理
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f xianyu-app
```

### 数据管理
```bash
# 备份数据
docker-compose exec xianyu-app cp /app/data/xianyu_data.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db

# 进入容器
docker-compose exec xianyu-app bash

# 查看数据目录
docker-compose exec xianyu-app ls -la /app/data/
```

### 故障排除
```bash
# 重新构建镜像
docker-compose build --no-cache

# 查看容器资源使用
docker stats

# 清理未使用的镜像
docker image prune

# 查看详细错误
docker-compose logs --tail=50 xianyu-app
```

## 🔍 故障排除

### 1. 容器启动失败
```bash
# 查看详细日志
docker-compose logs xianyu-app

# 检查端口占用
netstat -tulpn | grep 8080

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 2. 图形验证码不显示
```bash
# 检查Pillow安装
docker-compose exec xianyu-app python -c "from PIL import Image; print('OK')"

# 检查字体
docker-compose exec xianyu-app ls /usr/share/fonts/

# 重新构建镜像
docker-compose build --no-cache
```

### 3. 数据库问题
```bash
# 检查数据库文件
docker-compose exec xianyu-app ls -la /app/data/

# 运行数据迁移
docker-compose exec xianyu-app python migrate_to_multiuser.py

# 检查数据库状态
docker-compose exec xianyu-app python migrate_to_multiuser.py check
```

### 4. 权限问题
```bash
# 检查数据目录权限
ls -la ./data/

# 修复权限（Linux/Mac）
sudo chown -R 1000:1000 ./data ./logs

# Windows用户通常不需要修改权限
```

## 📊 监控和维护

### 性能监控
```bash
# 查看资源使用
docker stats --no-stream

# 查看容器详情
docker-compose exec xianyu-app ps aux

# 查看磁盘使用
docker-compose exec xianyu-app df -h
```

### 日志管理
```bash
# 查看日志大小
docker-compose exec xianyu-app du -sh /app/logs/

# 清理旧日志（保留最近7天）
docker-compose exec xianyu-app find /app/logs/ -name "*.log" -mtime +7 -delete

# 实时监控日志
docker-compose logs -f --tail=100
```

### 数据备份
```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T xianyu-app cp /app/data/xianyu_data.db /app/data/backup_$DATE.db
echo "备份完成: backup_$DATE.db"
EOF

chmod +x backup.sh
./backup.sh
```

## 🔐 安全建议

### 1. 修改默认配置
- ✅ 修改管理员密码
- ✅ 修改JWT密钥
- ✅ 禁用调试模式
- ✅ 配置防火墙

### 2. 网络安全
```bash
# 只允许本地访问（如果不需要外部访问）
# 修改 docker-compose.yml 中的端口映射
ports:
  - "127.0.0.1:8080:8080"  # 只绑定本地
```

### 3. 数据安全
- 定期备份数据库
- 使用HTTPS（通过反向代理）
- 限制用户注册（如不需要）
- 监控异常登录

## 🎉 部署完成

部署完成后，您的系统将支持：

- ✅ **多用户注册和登录**
- ✅ **图形验证码保护**
- ✅ **邮箱验证码验证**
- ✅ **完整的数据隔离**
- ✅ **企业级安全保护**

现在可以安全地支持多个用户同时使用系统！

## 📞 获取帮助

如果遇到问题：

1. 查看日志：`docker-compose logs -f`
2. 检查状态：`docker-compose ps`
3. 健康检查：`curl http://localhost:8080/health`
4. 运行测试：`python test_docker_deployment.sh`（Windows用户需要WSL或Git Bash）

---

**提示**: 首次部署后建议运行数据迁移脚本，将历史数据绑定到admin用户。
