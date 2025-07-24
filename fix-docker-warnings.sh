#!/bin/bash

# 修复Docker部署警告的快速脚本
# 解决version过时和.env文件缺失问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "========================================"
echo "  Docker部署警告修复脚本"
echo "========================================"
echo ""

# 1. 检查并创建.env文件
print_info "检查 .env 文件..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_info "从 .env.example 创建 .env 文件..."
        cp .env.example .env
        print_success ".env 文件已创建"
    else
        print_warning ".env.example 文件不存在"
        print_info "创建基本的 .env 文件..."
        cat > .env << 'EOF'
# 闲鱼自动回复系统 Docker 环境变量配置文件

# 基础配置
TZ=Asia/Shanghai
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO

# 数据库配置
DB_PATH=/app/data/xianyu_data.db

# 服务配置
WEB_PORT=8080

# 安全配置
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET_KEY=xianyu-auto-reply-secret-key-2024

# 资源限制
MEMORY_LIMIT=512
CPU_LIMIT=0.5
MEMORY_RESERVATION=256
CPU_RESERVATION=0.25

# 自动回复配置
AUTO_REPLY_ENABLED=true
WEBSOCKET_URL=wss://wss-goofish.dingtalk.com/
HEARTBEAT_INTERVAL=15
TOKEN_REFRESH_INTERVAL=3600
EOF
        print_success "基本 .env 文件已创建"
    fi
else
    print_success ".env 文件已存在"
fi

# 2. 检查docker-compose.yml版本问题
print_info "检查 docker-compose.yml 配置..."
if grep -q "^version:" docker-compose.yml 2>/dev/null; then
    print_warning "发现过时的 version 字段"
    print_info "移除 version 字段..."
    
    # 备份原文件
    cp docker-compose.yml docker-compose.yml.backup
    
    # 移除version行
    sed -i '/^version:/d' docker-compose.yml
    sed -i '/^$/N;/^\n$/d' docker-compose.yml  # 移除空行
    
    print_success "已移除过时的 version 字段"
    print_info "原文件已备份为 docker-compose.yml.backup"
else
    print_success "docker-compose.yml 配置正确"
fi

# 3. 检查env_file配置
print_info "检查 env_file 配置..."
if grep -A1 "env_file:" docker-compose.yml | grep -q "required: false"; then
    print_success "env_file 配置正确"
else
    print_info "更新 env_file 配置为可选..."
    
    # 备份文件（如果还没备份）
    if [ ! -f "docker-compose.yml.backup" ]; then
        cp docker-compose.yml docker-compose.yml.backup
    fi
    
    # 更新env_file配置
    sed -i '/env_file:/,+1c\
    env_file:\
      - path: .env\
        required: false' docker-compose.yml
    
    print_success "env_file 配置已更新"
fi

# 4. 验证修复结果
print_info "验证修复结果..."

echo ""
print_info "测试 Docker Compose 配置..."
if docker-compose config >/dev/null 2>&1; then
    print_success "Docker Compose 配置验证通过"
else
    print_error "Docker Compose 配置验证失败"
    echo "请检查 docker-compose.yml 文件"
    exit 1
fi

echo ""
print_success "所有警告已修复！"
echo ""
print_info "现在可以正常使用以下命令："
echo "  docker-compose up -d     # 启动服务"
echo "  docker-compose ps        # 查看状态"
echo "  docker-compose logs -f   # 查看日志"
echo ""
print_info "如果需要恢复原配置："
echo "  mv docker-compose.yml.backup docker-compose.yml"
