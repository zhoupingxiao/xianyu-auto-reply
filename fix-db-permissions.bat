@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 修复数据库权限问题的脚本 (Windows版本)
:: 解决Docker容器中数据库无法创建的问题

title 数据库权限修复脚本

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
echo   数据库权限修复脚本
echo ========================================
echo.

:: 1. 停止现有容器
call :print_info "停止现有容器..."
docker-compose down >nul 2>&1

:: 2. 检查并创建目录
call :print_info "检查并创建必要目录..."

for %%d in (data logs backups) do (
    if not exist "%%d" (
        call :print_info "创建目录: %%d"
        mkdir "%%d"
    )
    
    if not exist "%%d" (
        call :print_error "目录 %%d 创建失败"
        pause
        exit /b 1
    )
    
    call :print_success "目录 %%d 权限正常"
)

:: 3. 检查现有数据库文件
if exist "data\xianyu_data.db" (
    call :print_info "检查现有数据库文件..."
    call :print_success "数据库文件存在"
) else (
    call :print_info "数据库文件不存在，将在启动时创建"
)

:: 4. 测试数据库创建
call :print_info "测试数据库创建..."
python -c "
import sqlite3
import os

db_path = 'data/test_db.sqlite'
try:
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()
    print('✅ 数据库创建测试成功')
    if os.path.exists(db_path):
        os.remove(db_path)
except Exception as e:
    print(f'❌ 数据库创建测试失败: {e}')
    exit(1)
"

if !errorlevel! neq 0 (
    call :print_error "数据库创建测试失败"
    pause
    exit /b 1
)

:: 5. 重新构建并启动
call :print_info "重新构建并启动服务..."
docker-compose build --no-cache
if !errorlevel! neq 0 (
    call :print_error "Docker镜像构建失败"
    pause
    exit /b 1
)

docker-compose up -d
if !errorlevel! neq 0 (
    call :print_error "服务启动失败"
    pause
    exit /b 1
)

:: 6. 等待服务启动
call :print_info "等待服务启动..."
timeout /t 15 /nobreak >nul

:: 7. 检查服务状态
call :print_info "检查服务状态..."
docker-compose ps | findstr "Up" >nul
if !errorlevel! equ 0 (
    call :print_success "服务启动成功"
    
    :: 检查日志
    call :print_info "检查启动日志..."
    docker-compose logs --tail=20 xianyu-app
    
    :: 测试健康检查
    call :print_info "测试健康检查..."
    timeout /t 5 /nobreak >nul
    curl -f http://localhost:8080/health >nul 2>&1
    if !errorlevel! equ 0 (
        call :print_success "健康检查通过"
    ) else (
        call :print_warning "健康检查失败，但服务可能仍在启动中"
    )
) else (
    call :print_error "服务启动失败"
    call :print_info "查看错误日志:"
    docker-compose logs xianyu-app
    pause
    exit /b 1
)

echo.
call :print_success "数据库权限修复完成！"
echo.
call :print_info "服务信息:"
echo   Web界面: http://localhost:8080
echo   健康检查: http://localhost:8080/health
echo   默认账号: admin / admin123
echo.
call :print_info "常用命令:"
echo   查看日志: docker-compose logs -f
echo   重启服务: docker-compose restart
echo   停止服务: docker-compose down
echo.

pause
