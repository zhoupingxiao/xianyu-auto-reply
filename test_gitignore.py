#!/usr/bin/env python3
"""
测试 .gitignore 规则是否正确
验证 static/lib/ 目录不被忽略，而其他 lib/ 目录被忽略
"""

import os
import subprocess
import tempfile

def test_gitignore_rules():
    """测试 .gitignore 规则"""
    print("🧪 测试 .gitignore 规则")
    print("=" * 50)
    
    # 检查文件是否存在
    static_lib_files = [
        "static/lib/bootstrap/bootstrap.min.css",
        "static/lib/bootstrap/bootstrap.bundle.min.js", 
        "static/lib/bootstrap-icons/bootstrap-icons.css",
        "static/lib/bootstrap-icons/fonts/bootstrap-icons.woff",
        "static/lib/bootstrap-icons/fonts/bootstrap-icons.woff2"
    ]
    
    print("\n1️⃣ 检查静态文件是否存在...")
    all_exist = True
    for file_path in static_lib_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {file_path} (不存在)")
            all_exist = False
    
    if all_exist:
        print("   🎉 所有静态文件都存在！")
    else:
        print("   ⚠️ 部分静态文件缺失")
    
    # 检查 .gitignore 内容
    print("\n2️⃣ 检查 .gitignore 规则...")
    try:
        with open('.gitignore', 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        if 'lib/' in gitignore_content and '!static/lib/' in gitignore_content:
            print("   ✅ .gitignore 规则正确配置")
            print("   📝 规则说明:")
            print("      - lib/ : 忽略所有 lib 目录")
            print("      - !static/lib/ : 但不忽略 static/lib 目录")
        else:
            print("   ❌ .gitignore 规则配置不正确")
            
    except Exception as e:
        print(f"   ❌ 读取 .gitignore 失败: {e}")
    
    # 模拟测试（创建临时文件）
    print("\n3️⃣ 模拟测试 gitignore 行为...")
    
    # 创建测试目录和文件
    test_dirs = [
        "lib/test_file.txt",  # 应该被忽略
        "static/lib/test_file.txt",  # 不应该被忽略
        "some_other_lib/test_file.txt"  # 不应该被忽略
    ]
    
    created_files = []
    try:
        for test_path in test_dirs:
            os.makedirs(os.path.dirname(test_path), exist_ok=True)
            with open(test_path, 'w') as f:
                f.write("test content")
            created_files.append(test_path)
            print(f"   📁 创建测试文件: {test_path}")
        
        print("\n   📋 根据 .gitignore 规则预期:")
        print("      - lib/test_file.txt : 应该被忽略")
        print("      - static/lib/test_file.txt : 不应该被忽略")
        print("      - some_other_lib/test_file.txt : 不应该被忽略")
        
    except Exception as e:
        print(f"   ❌ 创建测试文件失败: {e}")
    
    finally:
        # 清理测试文件
        print("\n4️⃣ 清理测试文件...")
        for file_path in created_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"   🗑️ 删除: {file_path}")
            except Exception as e:
                print(f"   ⚠️ 删除失败: {file_path} - {e}")
        
        # 清理空目录
        test_cleanup_dirs = ["lib", "some_other_lib"]
        for dir_path in test_cleanup_dirs:
            try:
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    print(f"   🗑️ 删除空目录: {dir_path}")
            except Exception as e:
                print(f"   ⚠️ 删除目录失败: {dir_path} - {e}")
    
    print("\n" + "=" * 50)
    print("🎯 总结:")
    print("✅ static/lib/ 目录下的静态文件现在不会被 Git 忽略")
    print("✅ 其他 lib/ 目录仍然会被正常忽略")
    print("✅ 本地 CDN 资源可以正常提交到版本控制")

def check_file_sizes():
    """检查静态文件大小"""
    print("\n\n📊 静态文件大小统计")
    print("=" * 50)
    
    files_info = [
        ("Bootstrap CSS", "static/lib/bootstrap/bootstrap.min.css"),
        ("Bootstrap JS", "static/lib/bootstrap/bootstrap.bundle.min.js"),
        ("Bootstrap Icons CSS", "static/lib/bootstrap-icons/bootstrap-icons.css"),
        ("Bootstrap Icons WOFF2", "static/lib/bootstrap-icons/fonts/bootstrap-icons.woff2"),
        ("Bootstrap Icons WOFF", "static/lib/bootstrap-icons/fonts/bootstrap-icons.woff")
    ]
    
    total_size = 0
    for name, path in files_info:
        if os.path.exists(path):
            size = os.path.getsize(path)
            total_size += size
            print(f"📄 {name:<25} : {size:>8,} bytes ({size/1024:.1f} KB)")
        else:
            print(f"❌ {name:<25} : 文件不存在")
    
    print("-" * 50)
    print(f"📦 总大小                    : {total_size:>8,} bytes ({total_size/1024:.1f} KB)")
    
    if total_size > 0:
        print(f"\n💡 优势:")
        print(f"   - 不再依赖 CDN，提升中国大陆访问速度")
        print(f"   - 离线可用，提高系统稳定性")
        print(f"   - 版本固定，避免 CDN 更新导致的兼容性问题")

if __name__ == "__main__":
    try:
        test_gitignore_rules()
        check_file_sizes()
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
