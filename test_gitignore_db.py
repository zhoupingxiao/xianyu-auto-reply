#!/usr/bin/env python3
"""
测试 .gitignore 数据库文件忽略规则
"""

import os
import tempfile

def test_database_gitignore():
    """测试数据库文件忽略规则"""
    print("🧪 测试数据库文件 .gitignore 规则")
    print("=" * 50)
    
    # 检查当前项目中的数据库文件
    print("\n1️⃣ 检查项目中的数据库文件...")
    
    db_patterns = ["*.db", "*.sqlite", "*.sqlite3"]
    found_db_files = []
    
    for root, dirs, files in os.walk("."):
        for file in files:
            file_path = os.path.join(root, file)
            for pattern in db_patterns:
                if file.endswith(pattern.replace("*", "")):
                    size = os.path.getsize(file_path)
                    found_db_files.append((file_path, size))
                    print(f"   📄 {file_path} ({size:,} bytes)")
    
    if found_db_files:
        print(f"   📊 找到 {len(found_db_files)} 个数据库文件")
    else:
        print("   ✅ 未找到数据库文件")
    
    # 检查 .gitignore 规则
    print("\n2️⃣ 检查 .gitignore 数据库规则...")
    try:
        with open('.gitignore', 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        db_rules = ['*.db', '*.sqlite', '*.sqlite3']
        missing_rules = []
        
        for rule in db_rules:
            if rule in gitignore_content:
                print(f"   ✅ {rule} - 已配置")
            else:
                print(f"   ❌ {rule} - 未配置")
                missing_rules.append(rule)
        
        if not missing_rules:
            print("   🎉 所有数据库文件规则都已正确配置！")
        else:
            print(f"   ⚠️ 缺少规则: {missing_rules}")
            
    except Exception as e:
        print(f"   ❌ 读取 .gitignore 失败: {e}")
    
    # 测试其他新增的忽略规则
    print("\n3️⃣ 检查其他新增的忽略规则...")
    
    other_rules = [
        ("临时文件", ["*.tmp", "*.temp", "temp/", "tmp/"]),
        ("操作系统文件", [".DS_Store", "Thumbs.db"]),
        ("IDE文件", [".vscode/", ".idea/", "*.swp"]),
        ("环境文件", [".env", ".env.local"])
    ]
    
    for category, rules in other_rules:
        print(f"\n   📂 {category}:")
        for rule in rules:
            if rule in gitignore_content:
                print(f"      ✅ {rule}")
            else:
                print(f"      ❌ {rule}")
    
    # 模拟创建测试文件
    print("\n4️⃣ 模拟测试文件创建...")
    
    test_files = [
        "test.db",
        "test.sqlite", 
        "test.sqlite3",
        "test.tmp",
        ".env",
        "temp/test.txt"
    ]
    
    created_files = []
    try:
        for test_file in test_files:
            # 创建目录（如果需要）
            dir_path = os.path.dirname(test_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # 创建文件
            with open(test_file, 'w') as f:
                f.write("test content")
            created_files.append(test_file)
            print(f"   📁 创建测试文件: {test_file}")
        
        print("\n   📋 这些文件应该被 .gitignore 忽略:")
        for file in test_files:
            print(f"      - {file}")
        
    except Exception as e:
        print(f"   ❌ 创建测试文件失败: {e}")
    
    finally:
        # 清理测试文件
        print("\n5️⃣ 清理测试文件...")
        for file_path in created_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"   🗑️ 删除: {file_path}")
            except Exception as e:
                print(f"   ⚠️ 删除失败: {file_path} - {e}")
        
        # 清理测试目录
        if os.path.exists("temp") and not os.listdir("temp"):
            os.rmdir("temp")
            print("   🗑️ 删除空目录: temp")
    
    print("\n" + "=" * 50)
    print("🎯 .gitignore 数据库文件忽略规则测试完成！")

def show_gitignore_summary():
    """显示 .gitignore 规则总结"""
    print("\n\n📋 .gitignore 规则总结")
    print("=" * 50)
    
    categories = {
        "Python 相关": [
            "__pycache__", "*.so", ".Python", "build/", "dist/", 
            "*.egg-info/", "__pypackages__/", ".venv", "venv/", "ENV/"
        ],
        "数据库文件": [
            "*.db", "*.sqlite", "*.sqlite3", "db.sqlite3"
        ],
        "静态资源": [
            "lib/ (但不包括 static/lib/)"
        ],
        "临时文件": [
            "*.tmp", "*.temp", "temp/", "tmp/", "*.log", ".cache"
        ],
        "操作系统": [
            ".DS_Store", "Thumbs.db", "ehthumbs.db"
        ],
        "IDE 和编辑器": [
            ".vscode/", ".idea/", "*.swp", "*.swo", "*~"
        ],
        "环境配置": [
            ".env", ".env.local", ".env.*.local", "local_settings.py"
        ],
        "Node.js": [
            "*node_modules/*"
        ]
    }
    
    for category, rules in categories.items():
        print(f"\n📂 {category}:")
        for rule in rules:
            print(f"   • {rule}")
    
    print(f"\n💡 特别说明:")
    print(f"   • static/lib/ 目录不被忽略，用于存放本地 CDN 资源")
    print(f"   • 数据库文件被忽略，避免敏感数据泄露")
    print(f"   • 环境配置文件被忽略，保护敏感配置信息")

if __name__ == "__main__":
    try:
        test_database_gitignore()
        show_gitignore_summary()
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
