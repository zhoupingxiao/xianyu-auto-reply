@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 闲鱼自动回复系统 Docker 部署脚本 (Windows版本)
:: 支持快速部署和管理

set PROJECT_NAME=xianyu-auto-reply
set COMPOSE_FILE=docker-compose.yml
set ENV_FILE=.env

:: 颜色定义 (Windows 10+ 支持ANSI颜色)
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

:: 打印带颜色的消息
:print_info
echo %BLUE%ℹ️  %~1%NC%
goto :eof

:print_success
echo %GREEN%✅ %~1%NC%
goto :eof

:print_warning
echo %YELLOW%⚠️  %~1%NC%
goto :eof

:print_error
echo %RED%❌ %~1%NC%
goto :eof

:: 检查依赖
:check_dependencies
call :print_info "检查系统依赖..."

docker --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker 未安装，请先安装 Docker Desktop"
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker Compose 未安装，请先安装 Docker Compose"
    exit /b 1
)

call :print_success "系统依赖检查通过"
goto :eof

:: 初始化配置
:init_config
call :print_info "初始化配置文件..."

if not exist "%ENV_FILE%" (
    if exist ".env.example" (
        copy ".env.example" "%ENV_FILE%" >nul
        call :print_success "已创建 %ENV_FILE% 配置文件"
    ) else (
        call :print_error ".env.example 文件不存在"
        exit /b 1
    )
) else (
    call :print_warning "%ENV_FILE% 已存在，跳过创建"
)

:: 创建必要的目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups
call :print_success "已创建必要的目录"
goto :eof

:: 构建镜像
:build_image
call :print_info "构建 Docker 镜像..."
docker-compose build --no-cache
if errorlevel 1 (
    call :print_error "镜像构建失败"
    exit /b 1
)
call :print_success "镜像构建完成"
goto :eof

:: 启动服务
:start_services
set "profile="
if "%~1"=="with-nginx" (
    set "profile=--profile with-nginx"
    call :print_info "启动服务（包含 Nginx）..."
) else (
    call :print_info "启动基础服务..."
)

docker-compose %profile% up -d
if errorlevel 1 (
    call :print_error "服务启动失败"
    exit /b 1
)
call :print_success "服务启动完成"

:: 等待服务就绪
call :print_info "等待服务就绪..."
timeout /t 10 /nobreak >nul

:: 检查服务状态
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    call :print_error "服务启动失败"
    docker-compose logs
    exit /b 1
) else (
    call :print_success "服务运行正常"
    call :show_access_info "%~1"
)
goto :eof

:: 停止服务
:stop_services
call :print_info "停止服务..."
docker-compose down
call :print_success "服务已停止"
goto :eof

:: 重启服务
:restart_services
call :print_info "重启服务..."
docker-compose restart
call :print_success "服务已重启"
goto :eof

:: 查看日志
:show_logs
if "%~1"=="" (
    docker-compose logs -f
) else (
    docker-compose logs -f "%~1"
)
goto :eof

:: 查看状态
:show_status
call :print_info "服务状态:"
docker-compose ps

call :print_info "资源使用:"
for /f "tokens=*" %%i in ('docker-compose ps -q') do (
    docker stats --no-stream %%i
)
goto :eof

:: 显示访问信息
:show_access_info
echo.
call :print_success "🎉 部署完成！"
echo.

if "%~1"=="with-nginx" (
    echo 📱 访问地址:
    echo    HTTP:  http://localhost
    echo    HTTPS: https://localhost ^(如果配置了SSL^)
) else (
    echo 📱 访问地址:
    echo    HTTP: http://localhost:8080
)

echo.
echo 🔐 默认登录信息:
echo    用户名: admin
echo    密码:   admin123
echo.
echo 📊 管理命令:
echo    查看状态: %~nx0 status
echo    查看日志: %~nx0 logs
echo    重启服务: %~nx0 restart
echo    停止服务: %~nx0 stop
echo.
goto :eof

:: 健康检查
:health_check
call :print_info "执行健康检查..."

set "url=http://localhost:8080/health"
set "max_attempts=30"
set "attempt=1"

:health_loop
curl -f -s "%url%" >nul 2>&1
if not errorlevel 1 (
    call :print_success "健康检查通过"
    goto :eof
)

call :print_info "等待服务就绪... (!attempt!/%max_attempts%)"
timeout /t 2 /nobreak >nul
set /a attempt+=1

if !attempt! leq %max_attempts% goto health_loop

call :print_error "健康检查失败"
exit /b 1

:: 备份数据
:backup_data
call :print_info "备份数据..."

for /f "tokens=2 delims==" %%i in ('wmic OS Get localdatetime /value') do set datetime=%%i
set backup_dir=backups\%datetime:~0,8%_%datetime:~8,6%
mkdir "%backup_dir%" 2>nul

:: 备份数据库
if exist "data\xianyu_data.db" (
    copy "data\xianyu_data.db" "%backup_dir%\" >nul
    call :print_success "数据库备份完成"
)

:: 备份配置
copy "%ENV_FILE%" "%backup_dir%\" >nul
copy "global_config.yml" "%backup_dir%\" >nul 2>&1

call :print_success "数据备份完成: %backup_dir%"
goto :eof

:: 显示帮助信息
:show_help
echo 闲鱼自动回复系统 Docker 部署脚本 ^(Windows版本^)
echo.
echo 用法: %~nx0 [命令] [选项]
echo.
echo 命令:
echo   init                初始化配置文件
echo   build               构建 Docker 镜像
echo   start [with-nginx]  启动服务^(可选包含 Nginx^)
echo   stop                停止服务
echo   restart             重启服务
echo   status              查看服务状态
echo   logs [service]      查看日志
echo   health              健康检查
echo   backup              备份数据
echo   help                显示帮助信息
echo.
echo 示例:
echo   %~nx0 init             # 初始化配置
echo   %~nx0 start            # 启动基础服务
echo   %~nx0 start with-nginx # 启动包含 Nginx 的服务
echo   %~nx0 logs xianyu-app  # 查看应用日志
echo.
goto :eof

:: 主函数
:main
if "%~1"=="init" (
    call :check_dependencies
    call :init_config
) else if "%~1"=="build" (
    call :check_dependencies
    call :build_image
) else if "%~1"=="start" (
    call :check_dependencies
    call :init_config
    call :build_image
    call :start_services "%~2"
) else if "%~1"=="stop" (
    call :stop_services
) else if "%~1"=="restart" (
    call :restart_services
) else if "%~1"=="status" (
    call :show_status
) else if "%~1"=="logs" (
    call :show_logs "%~2"
) else if "%~1"=="health" (
    call :health_check
) else if "%~1"=="backup" (
    call :backup_data
) else if "%~1"=="help" (
    call :show_help
) else if "%~1"=="-h" (
    call :show_help
) else if "%~1"=="--help" (
    call :show_help
) else if "%~1"=="" (
    call :print_info "快速部署模式"
    call :check_dependencies
    call :init_config
    call :build_image
    call :start_services
) else (
    call :print_error "未知命令: %~1"
    call :show_help
    exit /b 1
)

goto :eof

:: 执行主函数
call :main %*
