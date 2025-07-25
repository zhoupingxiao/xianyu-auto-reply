#!/bin/bash

# 快速修复WebSocket兼容性问题
# 解决 "extra_headers" 参数不支持的问题

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔧 WebSocket兼容性问题修复"
echo "================================"

# 1. 检查当前websockets版本
print_info "检查当前websockets版本..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "未找到Python解释器"
    exit 1
fi

CURRENT_VERSION=$($PYTHON_CMD -c "import websockets; print(websockets.__version__)" 2>/dev/null || echo "未安装")
print_info "当前websockets版本: $CURRENT_VERSION"

# 2. 测试WebSocket兼容性
print_info "测试WebSocket兼容性..."
$PYTHON_CMD test-websocket-compatibility.py

# 3. 停止现有服务
print_info "停止现有Docker服务..."
docker-compose down 2>/dev/null || true

# 4. 更新websockets版本
print_info "更新websockets版本到兼容版本..."
if [ -f "requirements.txt" ]; then
    # 备份原文件
    cp requirements.txt requirements.txt.backup
    
    # 更新websockets版本
    sed -i 's/websockets>=.*/websockets>=10.0,<13.0  # 兼容性版本范围/' requirements.txt
    
    print_success "requirements.txt已更新"
else
    print_warning "requirements.txt文件不存在"
fi

# 5. 重新构建Docker镜像
print_info "重新构建Docker镜像..."
docker-compose build --no-cache

# 6. 启动服务
print_info "启动服务..."
docker-compose up -d

# 7. 等待服务启动
print_info "等待服务启动..."
sleep 15

# 8. 检查服务状态
print_info "检查服务状态..."
if docker-compose ps | grep -q "Up"; then
    print_success "✅ 服务启动成功！"
    
    # 检查WebSocket错误
    print_info "检查WebSocket连接状态..."
    sleep 5
    
    # 查看最近的日志
    echo ""
    print_info "最近的服务日志："
    docker-compose logs --tail=20 xianyu-app | grep -E "(WebSocket|extra_headers|ERROR)" || echo "未发现WebSocket相关错误"
    
    # 测试健康检查
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        print_success "健康检查通过"
    else
        print_warning "健康检查失败，服务可能仍在启动中"
    fi
    
else
    print_error "❌ 服务启动失败"
    print_info "查看错误日志:"
    docker-compose logs --tail=30 xianyu-app
    exit 1
fi

echo ""
print_success "🎉 WebSocket兼容性问题修复完成！"
echo ""
print_info "服务信息:"
echo "  Web界面: http://localhost:8080"
echo "  健康检查: http://localhost:8080/health"
echo "  默认账号: admin / admin123"
echo ""
print_info "如果仍有WebSocket问题，请："
echo "  1. 查看日志: docker-compose logs -f xianyu-app"
echo "  2. 运行测试: python test-websocket-compatibility.py"
echo "  3. 检查网络连接和防火墙设置"
