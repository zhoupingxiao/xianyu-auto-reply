#!/bin/bash

# ================================
# 闲鱼自动回复系统 - Docker重新构建脚本
# ================================

set -e

echo "🐳 闲鱼自动回复系统 - Docker重新构建"
echo "=================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

echo "📋 步骤1: 停止并删除现有容器"
echo "--------------------------------"

# 停止现有容器
if docker ps -q --filter "name=xianyu-auto-reply" | grep -q .; then
    echo "🛑 停止现有容器..."
    docker stop xianyu-auto-reply
fi

# 删除现有容器
if docker ps -aq --filter "name=xianyu-auto-reply" | grep -q .; then
    echo "🗑️ 删除现有容器..."
    docker rm xianyu-auto-reply
fi

echo "📋 步骤2: 删除现有镜像"
echo "--------------------------------"

# 删除现有镜像
if docker images -q xianyu-auto-reply | grep -q .; then
    echo "🗑️ 删除现有镜像..."
    docker rmi xianyu-auto-reply
fi

echo "📋 步骤3: 重新构建镜像"
echo "--------------------------------"

echo "🔨 开始构建新镜像..."
docker build -t xianyu-auto-reply .

echo "📋 步骤4: 启动新容器"
echo "--------------------------------"

echo "🚀 启动新容器..."
docker run -d \
    --name xianyu-auto-reply \
    --restart unless-stopped \
    -p 8080:8080 \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/backups:/app/backups" \
    -e DOCKER_ENV=true \
    xianyu-auto-reply

echo "📋 步骤5: 检查容器状态"
echo "--------------------------------"

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 5

# 检查容器状态
if docker ps --filter "name=xianyu-auto-reply" --filter "status=running" | grep -q xianyu-auto-reply; then
    echo "✅ 容器启动成功"
    
    echo "📋 容器信息:"
    docker ps --filter "name=xianyu-auto-reply" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo "📋 最近日志:"
    docker logs --tail 20 xianyu-auto-reply
    
    echo ""
    echo "🎉 Docker重新构建完成！"
    echo "=================================="
    echo "📱 Web界面: http://localhost:8080"
    echo "📊 健康检查: http://localhost:8080/health"
    echo "📋 查看日志: docker logs -f xianyu-auto-reply"
    echo "🛑 停止容器: docker stop xianyu-auto-reply"
    echo "🗑️ 删除容器: docker rm xianyu-auto-reply"
    
else
    echo "❌ 容器启动失败"
    echo "📋 错误日志:"
    docker logs xianyu-auto-reply
    exit 1
fi
