# Docker多用户系统部署更新

## 🎯 更新概述

为支持多用户系统和图形验证码功能，Docker部署配置已更新。

## 📦 新增依赖

### Python依赖
- **Pillow>=10.0.0** - 图像处理库，用于生成图形验证码

### 系统依赖
- **libjpeg-dev** - JPEG图像支持
- **libpng-dev** - PNG图像支持
- **libfreetype6-dev** - 字体渲染支持
- **fonts-dejavu-core** - 默认字体包

## 🔧 配置文件更新

### 1. requirements.txt
```diff
# AI回复相关
openai>=1.65.5
python-dotenv>=1.0.1

+ # 图像处理（图形验证码）
+ Pillow>=10.0.0
```

### 2. Dockerfile
```diff
# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nodejs \
        npm \
        tzdata \
        curl \
+       libjpeg-dev \
+       libpng-dev \
+       libfreetype6-dev \
+       fonts-dejavu-core \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*
```

### 3. docker-compose.yml
```diff
environment:
  - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
  - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
  - JWT_SECRET_KEY=${JWT_SECRET_KEY:-default-secret-key}
  - SESSION_TIMEOUT=${SESSION_TIMEOUT:-3600}
+ # 多用户系统配置
+ - MULTIUSER_ENABLED=${MULTIUSER_ENABLED:-true}
+ - USER_REGISTRATION_ENABLED=${USER_REGISTRATION_ENABLED:-true}
+ - EMAIL_VERIFICATION_ENABLED=${EMAIL_VERIFICATION_ENABLED:-true}
+ - CAPTCHA_ENABLED=${CAPTCHA_ENABLED:-true}
+ - TOKEN_EXPIRE_TIME=${TOKEN_EXPIRE_TIME:-86400}
```

## 🚀 部署步骤

### 1. 更新代码
```bash
# 拉取最新代码
git pull origin main

# 检查更新的文件
git status
```

### 2. 重新构建镜像
```bash
# 停止现有容器
docker-compose down

# 重新构建镜像（包含新依赖）
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```

### 3. 验证部署
```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs -f xianyu-app

# 健康检查
curl http://localhost:8080/health
```

## 🧪 功能测试

### 1. 访问注册页面
```bash
# 打开浏览器访问
http://localhost:8080/register.html
```

### 2. 测试图形验证码
- 页面应该自动显示图形验证码
- 点击图片可以刷新验证码
- 输入4位验证码应该能够验证

### 3. 测试用户注册
- 输入用户名和邮箱
- 验证图形验证码
- 发送邮箱验证码
- 完成注册流程

### 4. 测试数据隔离
- 注册多个用户
- 分别登录添加不同的Cookie
- 验证用户只能看到自己的数据

## 🔍 故障排除

### 1. 图形验证码不显示
```bash
# 检查Pillow是否正确安装
docker-compose exec xianyu-app python -c "from PIL import Image; print('Pillow OK')"

# 检查字体是否可用
docker-compose exec xianyu-app ls /usr/share/fonts/
```

### 2. 容器启动失败
```bash
# 查看详细错误日志
docker-compose logs xianyu-app

# 检查依赖安装
docker-compose exec xianyu-app pip list | grep -i pillow
```

### 3. 权限问题
```bash
# 检查数据目录权限
ls -la ./data/
ls -la ./logs/

# 修复权限（如需要）
sudo chown -R 1000:1000 ./data ./logs
```

## 📊 资源使用

### 更新后的资源需求
- **内存**: 512MB → 768MB（推荐）
- **磁盘**: 1GB → 1.5GB（推荐）
- **CPU**: 0.5核 → 0.5核（无变化）

### 调整资源限制
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 768M  # 增加内存限制
      cpus: '0.5'
    reservations:
      memory: 384M  # 增加内存预留
      cpus: '0.25'
```

## 🔐 安全配置

### 1. 环境变量安全
```bash
# 创建 .env 文件
cat > .env << EOF
# 修改默认密码
ADMIN_PASSWORD=your-secure-password

# 使用强JWT密钥
JWT_SECRET_KEY=your-very-long-and-random-secret-key

# 配置多用户功能
MULTIUSER_ENABLED=true
USER_REGISTRATION_ENABLED=true
EMAIL_VERIFICATION_ENABLED=true
CAPTCHA_ENABLED=true
EOF
```

### 2. 网络安全
```bash
# 如果不需要外部访问注册功能，可以禁用
USER_REGISTRATION_ENABLED=false

# 或者使用Nginx进行访问控制
# 参考 nginx/nginx.conf 配置
```

## 📋 迁移检查清单

- [ ] 更新 requirements.txt
- [ ] 更新 Dockerfile
- [ ] 更新 docker-compose.yml
- [ ] 重新构建镜像
- [ ] 测试图形验证码功能
- [ ] 测试用户注册流程
- [ ] 验证数据隔离
- [ ] 检查资源使用
- [ ] 更新监控配置

## 🎉 升级完成

升级完成后，您的系统将支持：

1. **多用户注册和登录**
2. **图形验证码保护**
3. **邮箱验证码验证**
4. **完整的数据隔离**
5. **企业级安全保护**

现在可以安全地支持多个用户同时使用系统，每个用户的数据完全独立！

## 📞 技术支持

如果在部署过程中遇到问题：

1. 查看容器日志：`docker-compose logs -f`
2. 检查健康状态：`docker-compose ps`
3. 验证网络连接：`curl http://localhost:8080/health`
4. 测试功能：访问 `http://localhost:8080/register.html`

---

**注意**: 首次部署多用户系统后，建议运行数据迁移脚本将历史数据绑定到admin用户。
