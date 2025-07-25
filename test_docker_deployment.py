#!/usr/bin/env python3
"""
Docker部署配置验证脚本
检查Docker部署是否包含所有必要的组件和配置
"""

import os
import sys
import yaml
import json
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"   ✅ {description}: {file_path}")
        return True
    else:
        print(f"   ❌ {description}: {file_path} (缺失)")
        return False

def check_requirements_txt():
    """检查requirements.txt中的依赖"""
    print("📦 检查Python依赖...")
    
    if not check_file_exists("requirements.txt", "依赖文件"):
        return False
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "loguru",
        "websockets",
        "aiohttp",
        "PyYAML",
        "PyExecJS",
        "blackboxprotobuf",
        "psutil",
        "requests",
        "python-multipart",
        "openai",
        "python-dotenv"
    ]
    
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        missing_packages = []
        for package in required_packages:
            if package.lower() not in content.lower():
                missing_packages.append(package)
        
        if missing_packages:
            print(f"   ❌ 缺失依赖: {', '.join(missing_packages)}")
            return False
        else:
            print(f"   ✅ 所有必要依赖都已包含 ({len(required_packages)} 个)")
            return True
            
    except Exception as e:
        print(f"   ❌ 读取requirements.txt失败: {e}")
        return False

def check_dockerfile():
    """检查Dockerfile配置"""
    print("\n🐳 检查Dockerfile...")
    
    if not check_file_exists("Dockerfile", "Docker镜像文件"):
        return False
    
    try:
        with open("Dockerfile", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_elements = [
            ("FROM python:", "Python基础镜像"),
            ("WORKDIR", "工作目录设置"),
            ("COPY requirements.txt", "依赖文件复制"),
            ("RUN pip install", "依赖安装"),
            ("EXPOSE", "端口暴露"),
            ("CMD", "启动命令")
        ]
        
        missing_elements = []
        for element, description in required_elements:
            if element not in content:
                missing_elements.append(description)
        
        if missing_elements:
            print(f"   ❌ 缺失配置: {', '.join(missing_elements)}")
            return False
        else:
            print(f"   ✅ Dockerfile配置完整")
            return True
            
    except Exception as e:
        print(f"   ❌ 读取Dockerfile失败: {e}")
        return False

def check_docker_compose():
    """检查docker-compose.yml配置"""
    print("\n🔧 检查Docker Compose配置...")
    
    if not check_file_exists("docker-compose.yml", "Docker Compose文件"):
        return False
    
    try:
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            compose_config = yaml.safe_load(f)
        
        # 检查服务配置
        if "services" not in compose_config:
            print("   ❌ 缺失services配置")
            return False
        
        services = compose_config["services"]
        if "xianyu-app" not in services:
            print("   ❌ 缺失xianyu-app服务")
            return False
        
        app_service = services["xianyu-app"]
        
        # 检查必要配置
        required_configs = [
            ("ports", "端口映射"),
            ("volumes", "数据挂载"),
            ("environment", "环境变量"),
            ("healthcheck", "健康检查")
        ]
        
        missing_configs = []
        for config, description in required_configs:
            if config not in app_service:
                missing_configs.append(description)
        
        if missing_configs:
            print(f"   ❌ 缺失配置: {', '.join(missing_configs)}")
            return False
        
        # 检查AI相关环境变量
        env_vars = app_service.get("environment", [])
        ai_env_vars = [
            "AI_REPLY_ENABLED",
            "DEFAULT_AI_MODEL",
            "DEFAULT_AI_BASE_URL",
            "AI_REQUEST_TIMEOUT"
        ]
        
        missing_ai_vars = []
        env_str = str(env_vars)
        for var in ai_env_vars:
            if var not in env_str:
                missing_ai_vars.append(var)
        
        if missing_ai_vars:
            print(f"   ⚠️  缺失AI环境变量: {', '.join(missing_ai_vars)}")
        else:
            print(f"   ✅ AI环境变量配置完整")
        
        print(f"   ✅ Docker Compose配置完整")
        return True
        
    except Exception as e:
        print(f"   ❌ 读取docker-compose.yml失败: {e}")
        return False

def check_env_example():
    """检查.env.example配置"""
    print("\n⚙️ 检查环境变量模板...")
    
    if not check_file_exists(".env.example", "环境变量模板"):
        return False
    
    try:
        with open(".env.example", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查AI相关配置
        ai_configs = [
            "AI_REPLY_ENABLED",
            "DEFAULT_AI_MODEL",
            "DEFAULT_AI_BASE_URL",
            "AI_REQUEST_TIMEOUT",
            "AI_MAX_TOKENS"
        ]
        
        missing_configs = []
        for config in ai_configs:
            if config not in content:
                missing_configs.append(config)
        
        if missing_configs:
            print(f"   ❌ 缺失AI配置: {', '.join(missing_configs)}")
            return False
        else:
            print(f"   ✅ AI配置完整")
        
        # 检查基础配置
        basic_configs = [
            "ADMIN_USERNAME",
            "ADMIN_PASSWORD",
            "JWT_SECRET_KEY",
            "AUTO_REPLY_ENABLED",
            "AUTO_DELIVERY_ENABLED"
        ]
        
        missing_basic = []
        for config in basic_configs:
            if config not in content:
                missing_basic.append(config)
        
        if missing_basic:
            print(f"   ❌ 缺失基础配置: {', '.join(missing_basic)}")
            return False
        else:
            print(f"   ✅ 基础配置完整")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 读取.env.example失败: {e}")
        return False

def check_documentation():
    """检查部署文档"""
    print("\n📚 检查部署文档...")
    
    docs = [
        ("Docker部署说明.md", "Docker部署说明"),
        ("README.md", "项目说明文档")
    ]
    
    all_exist = True
    for doc_file, description in docs:
        if not check_file_exists(doc_file, description):
            all_exist = False
    
    return all_exist

def check_directory_structure():
    """检查目录结构"""
    print("\n📁 检查目录结构...")
    
    required_dirs = [
        ("static", "静态文件目录"),
        ("templates", "模板目录（如果存在）")
    ]
    
    required_files = [
        ("Start.py", "主程序文件"),
        ("db_manager.py", "数据库管理"),
        ("XianyuAutoAsync.py", "闲鱼自动化"),
        ("ai_reply_engine.py", "AI回复引擎"),
        ("global_config.yml", "全局配置")
    ]
    
    all_exist = True
    
    # 检查目录
    for dir_name, description in required_dirs:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            print(f"   ✅ {description}: {dir_name}")
        else:
            if dir_name == "templates":  # templates是可选的
                print(f"   ⚠️  {description}: {dir_name} (可选)")
            else:
                print(f"   ❌ {description}: {dir_name} (缺失)")
                all_exist = False
    
    # 检查文件
    for file_name, description in required_files:
        if not check_file_exists(file_name, description):
            all_exist = False
    
    return all_exist

def main():
    """主检查函数"""
    print("🚀 Docker部署配置验证")
    print("=" * 50)
    
    checks = [
        ("Python依赖", check_requirements_txt),
        ("Dockerfile", check_dockerfile),
        ("Docker Compose", check_docker_compose),
        ("环境变量", check_env_example),
        ("目录结构", check_directory_structure),
        ("文档", check_documentation)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"   ❌ {check_name}检查异常: {e}")
            results.append((check_name, False))
    
    # 总结结果
    print("\n" + "=" * 50)
    print("📊 检查结果总结")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 总体评分: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有检查通过！Docker部署配置完整！")
        print("\n🚀 可以直接使用以下命令部署:")
        print("   docker-compose up -d")
    elif passed >= total * 0.8:
        print("\n⚠️  大部分检查通过，有少量问题需要修复")
        print("   建议修复上述问题后再部署")
    else:
        print("\n❌ 多项检查失败，需要完善配置后再部署")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
