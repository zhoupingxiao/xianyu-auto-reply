#!/bin/bash

# 快速修复Docker权限问题
# 这个脚本会立即解决权限问题并重启服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🚀 快速修复Docker权限问题"
echo "================================"

# 1. 停止容器
print_info "停止现有容器..."
docker-compose down

# 2. 确保目录存在并设置权限
print_info "设置目录权限..."
mkdir -p data logs backups
chmod 777 data logs backups

# 3. 检查并修复docker-compose.yml
print_info "检查docker-compose.yml配置..."
if ! grep -q "user.*0:0" docker-compose.yml; then
    print_info "添加root用户配置..."
    
    # 备份原文件
    cp docker-compose.yml docker-compose.yml.backup
    
    # 在container_name后添加user配置
    sed -i '/container_name: xianyu-auto-reply/a\    user: "0:0"' docker-compose.yml
    
    print_success "已配置使用root用户运行"
fi

# 4. 重新构建镜像
print_info "重新构建Docker镜像..."
docker-compose build --no-cache

# 5. 启动服务
print_info "启动服务..."
docker-compose up -d

# 6. 等待启动
print_info "等待服务启动..."
sleep 15

# 7. 检查状态
print_info "检查服务状态..."
if docker-compose ps | grep -q "Up"; then
    print_success "✅ 服务启动成功！"
    
    # 显示日志
    echo ""
    print_info "最近的日志："
    docker-compose logs --tail=10 xianyu-app
    
    echo ""
    print_success "🎉 权限问题已修复！"
    echo ""
    echo "访问信息："
    echo "  Web界面: http://localhost:8080"
    echo "  健康检查: http://localhost:8080/health"
    echo "  默认账号: admin / admin123"
    
else
    print_error "❌ 服务启动失败"
    echo ""
    print_info "错误日志："
    docker-compose logs xianyu-app
fi
