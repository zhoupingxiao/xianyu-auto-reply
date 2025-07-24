@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 快速修复Docker权限问题 (Windows版本)

title 快速修复Docker权限问题

:: 颜色定义
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

:print_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:print_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

echo 🚀 快速修复Docker权限问题
echo ================================
echo.

:: 1. 停止容器
call :print_info "停止现有容器..."
docker-compose down >nul 2>&1

:: 2. 确保目录存在
call :print_info "创建必要目录..."
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

:: 3. 检查并修复docker-compose.yml
call :print_info "检查docker-compose.yml配置..."
findstr /C:"user.*0:0" docker-compose.yml >nul 2>&1
if !errorlevel! neq 0 (
    call :print_info "添加root用户配置..."
    
    REM 备份原文件
    copy docker-compose.yml docker-compose.yml.backup >nul
    
    REM 创建临时文件添加user配置
    (
    for /f "tokens=*" %%a in (docker-compose.yml) do (
        echo %%a
        echo %%a | findstr /C:"container_name: xianyu-auto-reply" >nul
        if !errorlevel! equ 0 (
            echo     user: "0:0"
        )
    )
    ) > docker-compose.yml.tmp
    
    REM 替换原文件
    move docker-compose.yml.tmp docker-compose.yml >nul
    
    call :print_success "已配置使用root用户运行"
)

:: 4. 重新构建镜像
call :print_info "重新构建Docker镜像..."
docker-compose build --no-cache
if !errorlevel! neq 0 (
    call :print_error "Docker镜像构建失败"
    pause
    exit /b 1
)

:: 5. 启动服务
call :print_info "启动服务..."
docker-compose up -d
if !errorlevel! neq 0 (
    call :print_error "服务启动失败"
    pause
    exit /b 1
)

:: 6. 等待启动
call :print_info "等待服务启动..."
timeout /t 15 /nobreak >nul

:: 7. 检查状态
call :print_info "检查服务状态..."
docker-compose ps | findstr "Up" >nul
if !errorlevel! equ 0 (
    call :print_success "✅ 服务启动成功！"
    
    echo.
    call :print_info "最近的日志："
    docker-compose logs --tail=10 xianyu-app
    
    echo.
    call :print_success "🎉 权限问题已修复！"
    echo.
    echo 访问信息：
    echo   Web界面: http://localhost:8080
    echo   健康检查: http://localhost:8080/health
    echo   默认账号: admin / admin123
    
) else (
    call :print_error "❌ 服务启动失败"
    echo.
    call :print_info "错误日志："
    docker-compose logs xianyu-app
)

echo.
pause
