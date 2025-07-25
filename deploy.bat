@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 闲鱼自动回复系统 Docker 部署脚本 (Windows版本)
:: 作者: Xianyu Auto Reply System
:: 版本: 1.0.0

title 闲鱼自动回复系统 Docker 部署

:: 颜色定义
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

:: 打印带颜色的消息
:print_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:print_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:: 检查Docker是否安装
:check_docker
call :print_info "检查 Docker 环境..."

docker --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker 未安装，请先安装 Docker Desktop"
    echo.
    echo 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker Compose 未安装，请先安装 Docker Compose"
    pause
    exit /b 1
)

call :print_success "Docker 环境检查通过"
goto :eof

:: 创建必要的目录
:create_directories
call :print_info "创建必要的目录..."

if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups
if not exist "nginx" mkdir nginx
if not exist "nginx\ssl" mkdir nginx\ssl

REM 检查目录是否创建成功
if not exist "data" (
    call :print_error "data目录创建失败"
    pause
    exit /b 1
)

if not exist "logs" (
    call :print_error "logs目录创建失败"
    pause
    exit /b 1
)

call :print_success "目录创建完成"
goto :eof

:: 生成默认配置文件
:generate_config
REM 生成.env文件
if not exist ".env" (
    if exist ".env.example" (
        call :print_info "从模板生成 .env 文件..."
        copy ".env.example" ".env" >nul
        call :print_success ".env 文件已生成"
    ) else (
        call :print_warning ".env.example 文件不存在，跳过 .env 文件生成"
    )
) else (
    call :print_info ".env 文件已存在，跳过生成"
)

REM 生成global_config.yml文件
if exist "global_config.yml" (
    call :print_info "配置文件已存在，跳过生成"
    goto :eof
)

call :print_info "生成默认配置文件..."

(
echo # 闲鱼自动回复系统配置文件
echo API_ENDPOINTS:
echo   login_check: https://passport.goofish.com/newlogin/hasLogin.do
echo   message_headinfo: https://h5api.m.goofish.com/h5/mtop.idle.trade.pc.message.headinfo/1.0/
echo   token: https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/
echo.
echo APP_CONFIG:
echo   api_version: '1.0'
echo   app_key: 444e9908a51d1cb236a27862abc769c9
echo   app_version: '1.0'
echo   platform: web
echo.
echo AUTO_REPLY:
echo   enabled: true
echo   default_message: '亲爱的"{send_user_name}" 老板你好！所有宝贝都可以拍，秒发货的哈~不满意的话可以直接申请退款哈~'
echo   max_retry: 3
echo   retry_interval: 5
echo   api:
echo     enabled: false
echo     host: 0.0.0.0  # 绑定所有网络接口，支持IP访问
echo     port: 8080     # Web服务端口
echo     url: http://0.0.0.0:8080/xianyu/reply
echo     timeout: 10
echo.
echo COOKIES:
echo   last_update_time: ''
echo   value: ''
echo.
echo DEFAULT_HEADERS:
echo   accept: application/json
echo   accept-language: zh-CN,zh;q=0.9
echo   cache-control: no-cache
echo   origin: https://www.goofish.com
echo   pragma: no-cache
echo   referer: https://www.goofish.com/
echo   user-agent: Mozilla/5.0 ^(Windows NT 10.0; Win64; x64^) AppleWebKit/537.36 ^(KHTML, like Gecko^) Chrome/119.0.0.0 Safari/537.36
echo.
echo WEBSOCKET_URL: wss://wss-goofish.dingtalk.com/
echo HEARTBEAT_INTERVAL: 15
echo HEARTBEAT_TIMEOUT: 5
echo TOKEN_REFRESH_INTERVAL: 3600
echo TOKEN_RETRY_INTERVAL: 300
echo MESSAGE_EXPIRE_TIME: 300000
echo.
echo LOG_CONFIG:
echo   level: INFO
echo   format: '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}'
echo   rotation: '1 day'
echo   retention: '7 days'
) > global_config.yml

call :print_success "默认配置文件已生成"
goto :eof

:: 构建Docker镜像
:build_image
call :print_info "构建 Docker 镜像..."

docker build -t xianyu-auto-reply:latest .
if errorlevel 1 (
    call :print_error "Docker 镜像构建失败"
    pause
    exit /b 1
)

call :print_success "Docker 镜像构建完成"
goto :eof

:: 启动服务
:start_services
call :print_info "启动服务..."

if "%~1"=="--with-nginx" (
    call :print_info "启动服务（包含 Nginx）..."
    docker-compose --profile with-nginx up -d
) else (
    call :print_info "启动服务（不包含 Nginx）..."
    docker-compose up -d
)

if errorlevel 1 (
    call :print_error "服务启动失败"
    pause
    exit /b 1
)

call :print_success "服务启动完成"
goto :eof

:: 显示服务状态
:show_status
call :print_info "服务状态："
docker-compose ps

echo.
call :print_info "服务日志（最近10行）："
docker-compose logs --tail=10
goto :eof

:: 显示访问信息
:show_access_info
call :print_success "部署完成！"
echo.
call :print_info "访问信息："
echo   Web界面: http://localhost:8080
echo   默认账号: admin
echo   默认密码: admin123
echo.
call :print_info "常用命令："
echo   查看日志: docker-compose logs -f
echo   重启服务: docker-compose restart
echo   停止服务: docker-compose down
echo   更新服务: deploy.bat update
echo.
call :print_info "数据目录："
echo   数据库: .\data\xianyu_data.db
echo   日志: .\logs\
echo   配置: .\global_config.yml
echo.
goto :eof

:: 更新服务
:update_services
call :print_info "更新服务..."

docker-compose down
call :build_image
call :start_services %~1

call :print_success "服务更新完成"
goto :eof

:: 清理资源
:cleanup
call :print_warning "清理 Docker 资源..."

docker-compose down --volumes --remove-orphans
docker rmi xianyu-auto-reply:latest 2>nul

call :print_success "清理完成"
goto :eof

:: 显示帮助
:show_help
echo 使用方法:
echo   %~nx0                    # 首次部署
echo   %~nx0 with-nginx         # 部署并启动 Nginx
echo   %~nx0 update             # 更新服务
echo   %~nx0 update with-nginx  # 更新服务并启动 Nginx
echo   %~nx0 status             # 查看服务状态
echo   %~nx0 cleanup            # 清理所有资源
echo   %~nx0 help               # 显示帮助
goto :eof

:: 主函数
:main
echo ========================================
echo   闲鱼自动回复系统 Docker 部署脚本
echo ========================================
echo.

if "%~1"=="update" (
    call :print_info "更新模式"
    call :check_docker
    call :update_services %~2
    call :show_status
    call :show_access_info
) else if "%~1"=="cleanup" (
    call :print_warning "清理模式"
    call :cleanup
) else if "%~1"=="status" (
    call :show_status
) else if "%~1"=="help" (
    call :show_help
) else (
    call :print_info "首次部署模式"
    call :check_docker
    call :create_directories
    call :generate_config
    call :build_image
    call :start_services %~1
    call :show_status
    call :show_access_info
)

echo.
pause
goto :eof

:: 执行主函数
call :main %*
