#!/bin/bash

# 修复数据库权限问题的脚本
# 解决Docker容器中数据库无法创建的问题

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
echo "  数据库权限修复脚本"
echo "========================================"
echo ""

# 1. 停止现有容器
print_info "停止现有容器..."
docker-compose down 2>/dev/null || true

# 2. 检查并创建目录
print_info "检查并创建必要目录..."
for dir in data logs backups; do
    if [ ! -d "$dir" ]; then
        print_info "创建目录: $dir"
        mkdir -p "$dir"
    fi
    
    # 设置权限
    chmod 755 "$dir"
    
    # 检查权限
    if [ ! -w "$dir" ]; then
        print_error "目录 $dir 没有写权限"
        
        # 尝试修复权限
        print_info "尝试修复权限..."
        sudo chmod 755 "$dir" 2>/dev/null || {
            print_error "无法修复权限，请手动执行: sudo chmod 755 $dir"
            exit 1
        }
    fi
    
    print_success "目录 $dir 权限正常"
done

# 3. 检查现有数据库文件
if [ -f "data/xianyu_data.db" ]; then
    print_info "检查现有数据库文件权限..."
    if [ ! -w "data/xianyu_data.db" ]; then
        print_warning "数据库文件没有写权限，尝试修复..."
        chmod 644 "data/xianyu_data.db"
        print_success "数据库文件权限已修复"
    else
        print_success "数据库文件权限正常"
    fi
fi

# 4. 检查Docker用户映射
print_info "检查Docker用户映射..."
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

print_info "当前用户 UID:GID = $CURRENT_UID:$CURRENT_GID"

# 5. 创建测试数据库
print_info "测试数据库创建..."
python3 -c "
import sqlite3
import os

db_path = 'data/test_db.sqlite'
try:
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()
    print('✅ 数据库创建测试成功')
    os.remove(db_path)
except Exception as e:
    print(f'❌ 数据库创建测试失败: {e}')
    exit(1)
" || {
    print_error "数据库创建测试失败"
    exit 1
}

# 6. 更新docker-compose.yml用户映射
print_info "检查docker-compose.yml用户映射..."
if ! grep -q "user:" docker-compose.yml; then
    print_info "添加用户映射到docker-compose.yml..."
    
    # 备份原文件
    cp docker-compose.yml docker-compose.yml.backup
    
    # 在xianyu-app服务中添加user配置
    sed -i '/container_name: xianyu-auto-reply/a\    user: "'$CURRENT_UID':'$CURRENT_GID'"' docker-compose.yml
    
    print_success "用户映射已添加"
else
    print_info "用户映射已存在"
fi

# 7. 重新构建并启动
print_info "重新构建并启动服务..."
docker-compose build --no-cache
docker-compose up -d

# 8. 等待服务启动
print_info "等待服务启动..."
sleep 10

# 9. 检查服务状态
print_info "检查服务状态..."
if docker-compose ps | grep -q "Up"; then
    print_success "服务启动成功"
    
    # 检查日志
    print_info "检查启动日志..."
    docker-compose logs --tail=20 xianyu-app
    
    # 测试健康检查
    print_info "测试健康检查..."
    sleep 5
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        print_success "健康检查通过"
    else
        print_warning "健康检查失败，但服务可能仍在启动中"
    fi
else
    print_error "服务启动失败"
    print_info "查看错误日志:"
    docker-compose logs xianyu-app
    exit 1
fi

echo ""
print_success "数据库权限修复完成！"
echo ""
print_info "服务信息:"
echo "  Web界面: http://localhost:8080"
echo "  健康检查: http://localhost:8080/health"
echo "  默认账号: admin / admin123"
echo ""
print_info "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo "  停止服务: docker-compose down"
