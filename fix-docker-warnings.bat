@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 修复Docker部署警告的快速脚本 (Windows版本)
:: 解决version过时和.env文件缺失问题

title Docker部署警告修复脚本

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

echo ========================================
echo   Docker部署警告修复脚本
echo ========================================
echo.

:: 1. 检查并创建.env文件
call :print_info "检查 .env 文件..."
if not exist ".env" (
    if exist ".env.example" (
        call :print_info "从 .env.example 创建 .env 文件..."
        copy ".env.example" ".env" >nul
        call :print_success ".env 文件已创建"
    ) else (
        call :print_warning ".env.example 文件不存在"
        call :print_info "创建基本的 .env 文件..."
        
        (
        echo # 闲鱼自动回复系统 Docker 环境变量配置文件
        echo.
        echo # 基础配置
        echo TZ=Asia/Shanghai
        echo PYTHONUNBUFFERED=1
        echo LOG_LEVEL=INFO
        echo.
        echo # 数据库配置
        echo DB_PATH=/app/data/xianyu_data.db
        echo.
        echo # 服务配置
        echo WEB_PORT=8080
        echo.
        echo # 安全配置
        echo ADMIN_USERNAME=admin
        echo ADMIN_PASSWORD=admin123
        echo JWT_SECRET_KEY=xianyu-auto-reply-secret-key-2024
        echo.
        echo # 资源限制
        echo MEMORY_LIMIT=512
        echo CPU_LIMIT=0.5
        echo MEMORY_RESERVATION=256
        echo CPU_RESERVATION=0.25
        echo.
        echo # 自动回复配置
        echo AUTO_REPLY_ENABLED=true
        echo WEBSOCKET_URL=wss://wss-goofish.dingtalk.com/
        echo HEARTBEAT_INTERVAL=15
        echo TOKEN_REFRESH_INTERVAL=3600
        ) > .env
        
        call :print_success "基本 .env 文件已创建"
    )
) else (
    call :print_success ".env 文件已存在"
)

:: 2. 检查docker-compose.yml版本问题
call :print_info "检查 docker-compose.yml 配置..."
findstr /B "version:" docker-compose.yml >nul 2>&1
if !errorlevel! equ 0 (
    call :print_warning "发现过时的 version 字段"
    call :print_info "移除 version 字段..."
    
    REM 备份原文件
    copy docker-compose.yml docker-compose.yml.backup >nul
    
    REM 创建临时文件，移除version行
    (
    for /f "tokens=*" %%a in (docker-compose.yml) do (
        echo %%a | findstr /B "version:" >nul
        if !errorlevel! neq 0 (
            echo %%a
        )
    )
    ) > docker-compose.yml.tmp
    
    REM 替换原文件
    move docker-compose.yml.tmp docker-compose.yml >nul
    
    call :print_success "已移除过时的 version 字段"
    call :print_info "原文件已备份为 docker-compose.yml.backup"
) else (
    call :print_success "docker-compose.yml 配置正确"
)

:: 3. 验证修复结果
call :print_info "验证修复结果..."

echo.
call :print_info "测试 Docker Compose 配置..."
docker-compose config >nul 2>&1
if !errorlevel! equ 0 (
    call :print_success "Docker Compose 配置验证通过"
) else (
    call :print_error "Docker Compose 配置验证失败"
    echo 请检查 docker-compose.yml 文件
    pause
    exit /b 1
)

echo.
call :print_success "所有警告已修复！"
echo.
call :print_info "现在可以正常使用以下命令："
echo   docker-compose up -d     # 启动服务
echo   docker-compose ps        # 查看状态
echo   docker-compose logs -f   # 查看日志
echo.
call :print_info "如果需要恢复原配置："
echo   move docker-compose.yml.backup docker-compose.yml
echo.

pause
