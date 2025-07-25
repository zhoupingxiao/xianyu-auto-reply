#!/bin/bash

# Docker多用户系统部署测试脚本

echo "🚀 Docker多用户系统部署测试"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker和Docker Compose
echo -e "${BLUE}1. 检查Docker环境${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker环境检查通过${NC}"
echo "   Docker版本: $(docker --version)"
echo "   Docker Compose版本: $(docker-compose --version)"

# 检查必要文件
echo -e "\n${BLUE}2. 检查部署文件${NC}"
required_files=("Dockerfile" "docker-compose.yml" "requirements.txt")

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file 不存在${NC}"
        exit 1
    fi
done

# 检查新增依赖
echo -e "\n${BLUE}3. 检查新增依赖${NC}"
if grep -q "Pillow" requirements.txt; then
    echo -e "${GREEN}✅ Pillow依赖已添加${NC}"
else
    echo -e "${RED}❌ Pillow依赖缺失${NC}"
    exit 1
fi

# 停止现有容器
echo -e "\n${BLUE}4. 停止现有容器${NC}"
docker-compose down
echo -e "${GREEN}✅ 容器已停止${NC}"

# 构建镜像
echo -e "\n${BLUE}5. 构建Docker镜像${NC}"
echo "这可能需要几分钟时间..."
if docker-compose build --no-cache; then
    echo -e "${GREEN}✅ 镜像构建成功${NC}"
else
    echo -e "${RED}❌ 镜像构建失败${NC}"
    exit 1
fi

# 启动服务
echo -e "\n${BLUE}6. 启动服务${NC}"
if docker-compose up -d; then
    echo -e "${GREEN}✅ 服务启动成功${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi

# 等待服务就绪
echo -e "\n${BLUE}7. 等待服务就绪${NC}"
echo "等待30秒让服务完全启动..."
sleep 30

# 检查容器状态
echo -e "\n${BLUE}8. 检查容器状态${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ 容器运行正常${NC}"
    docker-compose ps
else
    echo -e "${RED}❌ 容器运行异常${NC}"
    docker-compose ps
    echo -e "\n${YELLOW}查看日志:${NC}"
    docker-compose logs --tail=20
    exit 1
fi

# 健康检查
echo -e "\n${BLUE}9. 健康检查${NC}"
max_attempts=10
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8080/health > /dev/null; then
        echo -e "${GREEN}✅ 健康检查通过${NC}"
        break
    else
        echo -e "${YELLOW}⏳ 尝试 $attempt/$max_attempts - 等待服务响应...${NC}"
        sleep 3
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo -e "${RED}❌ 健康检查失败${NC}"
    echo -e "\n${YELLOW}查看日志:${NC}"
    docker-compose logs --tail=20
    exit 1
fi

# 测试图形验证码API
echo -e "\n${BLUE}10. 测试图形验证码功能${NC}"
response=$(curl -s -X POST http://localhost:8080/generate-captcha \
    -H "Content-Type: application/json" \
    -d '{"session_id": "test_session"}')

if echo "$response" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ 图形验证码API正常${NC}"
else
    echo -e "${RED}❌ 图形验证码API异常${NC}"
    echo "响应: $response"
fi

# 测试注册页面
echo -e "\n${BLUE}11. 测试注册页面${NC}"
if curl -s http://localhost:8080/register.html | grep -q "用户注册"; then
    echo -e "${GREEN}✅ 注册页面可访问${NC}"
else
    echo -e "${RED}❌ 注册页面访问失败${NC}"
fi

# 测试登录页面
echo -e "\n${BLUE}12. 测试登录页面${NC}"
if curl -s http://localhost:8080/login.html | grep -q "登录"; then
    echo -e "${GREEN}✅ 登录页面可访问${NC}"
else
    echo -e "${RED}❌ 登录页面访问失败${NC}"
fi

# 检查Pillow安装
echo -e "\n${BLUE}13. 检查Pillow安装${NC}"
if docker-compose exec -T xianyu-app python -c "from PIL import Image; print('Pillow OK')" 2>/dev/null | grep -q "Pillow OK"; then
    echo -e "${GREEN}✅ Pillow安装正常${NC}"
else
    echo -e "${RED}❌ Pillow安装异常${NC}"
fi

# 检查字体支持
echo -e "\n${BLUE}14. 检查字体支持${NC}"
if docker-compose exec -T xianyu-app ls /usr/share/fonts/ 2>/dev/null | grep -q "dejavu"; then
    echo -e "${GREEN}✅ 字体支持正常${NC}"
else
    echo -e "${YELLOW}⚠️ 字体支持可能有问题${NC}"
fi

# 显示访问信息
echo -e "\n${GREEN}🎉 Docker部署测试完成！${NC}"
echo "=================================="
echo -e "${BLUE}访问信息:${NC}"
echo "• 主页: http://localhost:8080"
echo "• 登录页面: http://localhost:8080/login.html"
echo "• 注册页面: http://localhost:8080/register.html"
echo "• 健康检查: http://localhost:8080/health"
echo ""
echo -e "${BLUE}默认管理员账号:${NC}"
echo "• 用户名: admin"
echo "• 密码: admin123"
echo ""
echo -e "${BLUE}多用户功能:${NC}"
echo "• ✅ 用户注册"
echo "• ✅ 图形验证码"
echo "• ✅ 邮箱验证"
echo "• ✅ 数据隔离"
echo ""
echo -e "${YELLOW}管理命令:${NC}"
echo "• 查看日志: docker-compose logs -f"
echo "• 停止服务: docker-compose down"
echo "• 重启服务: docker-compose restart"
echo "• 查看状态: docker-compose ps"

# 可选：显示资源使用情况
echo -e "\n${BLUE}资源使用情况:${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep xianyu || echo "无法获取资源使用情况"

echo -e "\n${GREEN}部署测试完成！系统已就绪。${NC}"
