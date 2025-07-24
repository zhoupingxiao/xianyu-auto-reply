#!/bin/bash

# 闲鱼自动回复系统 Docker 部署脚本
# 作者: Xianyu Auto Reply System
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_success "Docker 环境检查通过"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."

    # 创建目录
    mkdir -p data
    mkdir -p logs
    mkdir -p backups
    mkdir -p nginx/ssl

    # 设置权限 (确保Docker容器可以写入)
    chmod 755 data logs backups

    # 检查权限
    if [ ! -w "data" ]; then
        print_error "data目录没有写权限"
        exit 1
    fi

    if [ ! -w "logs" ]; then
        print_error "logs目录没有写权限"
        exit 1
    fi

    print_success "目录创建完成"
}

# 生成默认配置文件
generate_config() {
    # 生成.env文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_info "从模板生成 .env 文件..."
            cp .env.example .env
            print_success ".env 文件已生成"
        else
            print_warning ".env.example 文件不存在，跳过 .env 文件生成"
        fi
    else
        print_info ".env 文件已存在，跳过生成"
    fi

    # 生成global_config.yml文件
    if [ ! -f "global_config.yml" ]; then
        print_info "生成默认配置文件..."
        
        cat > global_config.yml << EOF
# 闲鱼自动回复系统配置文件
API_ENDPOINTS:
  login_check: https://passport.goofish.com/newlogin/hasLogin.do
  message_headinfo: https://h5api.m.goofish.com/h5/mtop.idle.trade.pc.message.headinfo/1.0/
  token: https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/

APP_CONFIG:
  api_version: '1.0'
  app_key: 444e9908a51d1cb236a27862abc769c9
  app_version: '1.0'
  platform: web

AUTO_REPLY:
  enabled: true
  default_message: '亲爱的"{send_user_name}" 老板你好！所有宝贝都可以拍，秒发货的哈~不满意的话可以直接申请退款哈~'
  max_retry: 3
  retry_interval: 5
  api:
    enabled: false
    host: 0.0.0.0  # 绑定所有网络接口，支持IP访问
    port: 8080     # Web服务端口
    url: http://0.0.0.0:8080/xianyu/reply
    timeout: 10

COOKIES:
  last_update_time: ''
  value: ''

DEFAULT_HEADERS:
  accept: application/json
  accept-language: zh-CN,zh;q=0.9
  cache-control: no-cache
  origin: https://www.goofish.com
  pragma: no-cache
  referer: https://www.goofish.com/
  sec-ch-ua: '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"'
  sec-ch-ua-mobile: '?0'
  sec-ch-ua-platform: '"Windows"'
  sec-fetch-dest: empty
  sec-fetch-mode: cors
  sec-fetch-site: same-site
  user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36

WEBSOCKET_URL: wss://wss-goofish.dingtalk.com/
HEARTBEAT_INTERVAL: 15
HEARTBEAT_TIMEOUT: 5
TOKEN_REFRESH_INTERVAL: 3600
TOKEN_RETRY_INTERVAL: 300
MESSAGE_EXPIRE_TIME: 300000

LOG_CONFIG:
  level: INFO
  format: '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}'
  rotation: '1 day'
  retention: '7 days'
EOF
        
        print_success "默认配置文件已生成"
    else
        print_info "配置文件已存在，跳过生成"
    fi
}

# 构建Docker镜像
build_image() {
    print_info "构建 Docker 镜像..."
    
    docker build -t xianyu-auto-reply:latest .
    
    print_success "Docker 镜像构建完成"
}

# 启动服务
start_services() {
    print_info "启动服务..."
    
    # 检查是否需要启动 Nginx
    if [ "$1" = "--with-nginx" ]; then
        print_info "启动服务（包含 Nginx）..."
        docker-compose --profile with-nginx up -d
    else
        print_info "启动服务（不包含 Nginx）..."
        docker-compose up -d
    fi
    
    print_success "服务启动完成"
}

# 显示服务状态
show_status() {
    print_info "服务状态："
    docker-compose ps
    
    print_info "服务日志（最近10行）："
    docker-compose logs --tail=10
}

# 显示访问信息
show_access_info() {
    print_success "部署完成！"
    echo ""
    print_info "访问信息："
    echo "  Web界面: http://localhost:8080"
    echo "  默认账号: admin"
    echo "  默认密码: admin123"
    echo ""
    print_info "常用命令："
    echo "  查看日志: docker-compose logs -f"
    echo "  重启服务: docker-compose restart"
    echo "  停止服务: docker-compose down"
    echo "  更新服务: ./deploy.sh --update"
    echo ""
    print_info "数据目录："
    echo "  数据库: ./data/xianyu_data.db"
    echo "  日志: ./logs/"
    echo "  配置: ./global_config.yml"
}

# 更新服务
update_services() {
    print_info "更新服务..."
    
    # 停止服务
    docker-compose down
    
    # 重新构建镜像
    build_image
    
    # 启动服务
    start_services $1
    
    print_success "服务更新完成"
}

# 清理资源
cleanup() {
    print_warning "清理 Docker 资源..."
    
    # 停止并删除容器
    docker-compose down --volumes --remove-orphans
    
    # 删除镜像
    docker rmi xianyu-auto-reply:latest 2>/dev/null || true
    
    print_success "清理完成"
}

# 主函数
main() {
    echo "========================================"
    echo "  闲鱼自动回复系统 Docker 部署脚本"
    echo "========================================"
    echo ""
    
    case "$1" in
        --update)
            print_info "更新模式"
            check_docker
            update_services $2
            show_status
            show_access_info
            ;;
        --cleanup)
            print_warning "清理模式"
            cleanup
            ;;
        --status)
            show_status
            ;;
        --help)
            echo "使用方法:"
            echo "  $0                    # 首次部署"
            echo "  $0 --with-nginx       # 部署并启动 Nginx"
            echo "  $0 --update           # 更新服务"
            echo "  $0 --update --with-nginx  # 更新服务并启动 Nginx"
            echo "  $0 --status           # 查看服务状态"
            echo "  $0 --cleanup          # 清理所有资源"
            echo "  $0 --help             # 显示帮助"
            ;;
        *)
            print_info "首次部署模式"
            check_docker
            create_directories
            generate_config
            build_image
            start_services $1
            show_status
            show_access_info
            ;;
    esac
}

# 执行主函数
main "$@"
