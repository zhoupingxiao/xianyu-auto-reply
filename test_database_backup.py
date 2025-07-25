#!/usr/bin/env python3
"""
测试数据库备份和恢复功能
"""

import requests
import os
import time
import sqlite3
from loguru import logger

BASE_URL = "http://localhost:8080"

def test_admin_login():
    """测试管理员登录"""
    logger.info("测试管理员登录...")
    
    response = requests.post(f"{BASE_URL}/login", 
                           json={'username': 'admin', 'password': 'admin123'})
    
    if response.json()['success']:
        token = response.json()['token']
        user_id = response.json()['user_id']
        
        logger.info(f"管理员登录成功，token: {token[:20]}...")
        return {
            'token': token,
            'user_id': user_id,
            'headers': {'Authorization': f'Bearer {token}'}
        }
    else:
        logger.error("管理员登录失败")
        return None

def test_database_download(admin):
    """测试数据库下载"""
    logger.info("测试数据库下载...")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/backup/download", 
                              headers=admin['headers'])
        
        if response.status_code == 200:
            # 保存下载的文件
            timestamp = int(time.time())
            backup_filename = f"test_backup_{timestamp}.db"
            
            with open(backup_filename, 'wb') as f:
                f.write(response.content)
            
            # 验证下载的文件
            file_size = os.path.getsize(backup_filename)
            logger.info(f"✅ 数据库下载成功: {backup_filename} ({file_size} bytes)")
            
            # 验证是否为有效的SQLite数据库
            try:
                conn = sqlite3.connect(backup_filename)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                table_names = [table[0] for table in tables]
                logger.info(f"   数据库包含 {len(table_names)} 个表: {', '.join(table_names[:5])}...")
                
                return backup_filename
                
            except sqlite3.Error as e:
                logger.error(f"❌ 下载的文件不是有效的SQLite数据库: {e}")
                return None
                
        else:
            logger.error(f"❌ 数据库下载失败: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ 数据库下载异常: {e}")
        return None

def test_backup_file_list(admin):
    """测试备份文件列表"""
    logger.info("测试备份文件列表...")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/backup/list", 
                              headers=admin['headers'])
        
        if response.status_code == 200:
            data = response.json()
            backups = data.get('backups', [])
            logger.info(f"✅ 获取备份文件列表成功，共 {len(backups)} 个备份文件")
            
            for backup in backups[:3]:  # 显示前3个
                logger.info(f"   {backup['filename']} - {backup['size_mb']}MB - {backup['created_time']}")
            
            return True
        else:
            logger.error(f"❌ 获取备份文件列表失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 获取备份文件列表异常: {e}")
        return False

def test_database_upload(admin, backup_file):
    """测试数据库上传（模拟，不实际执行）"""
    logger.info("测试数据库上传准备...")
    
    if not backup_file or not os.path.exists(backup_file):
        logger.error("❌ 没有有效的备份文件进行上传测试")
        return False
    
    try:
        # 检查文件大小
        file_size = os.path.getsize(backup_file)
        if file_size > 100 * 1024 * 1024:  # 100MB
            logger.warning(f"⚠️ 备份文件过大: {file_size} bytes")
            return False
        
        # 验证文件格式
        try:
            conn = sqlite3.connect(backup_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            conn.close()
            
            logger.info(f"✅ 备份文件验证通过，包含 {user_count} 个用户")
            logger.info("   注意：实际上传会替换当前数据库，此处仅验证文件有效性")
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"❌ 备份文件验证失败: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 数据库上传准备异常: {e}")
        return False

def cleanup_test_files():
    """清理测试文件"""
    logger.info("清理测试文件...")
    
    import glob
    test_files = glob.glob("test_backup_*.db")
    
    for file_path in test_files:
        try:
            os.remove(file_path)
            logger.info(f"   删除测试文件: {file_path}")
        except Exception as e:
            logger.warning(f"   删除文件失败: {file_path} - {e}")

def main():
    """主测试函数"""
    print("🚀 数据库备份和恢复功能测试")
    print("=" * 60)
    
    print("📋 测试内容:")
    print("• 管理员登录")
    print("• 数据库备份下载")
    print("• 备份文件列表查询")
    print("• 备份文件验证")
    print("• 数据库上传准备（不实际执行）")
    
    try:
        # 管理员登录
        admin = test_admin_login()
        if not admin:
            print("❌ 测试失败：管理员登录失败")
            return False
        
        print("✅ 管理员登录成功")
        
        # 测试各项功能
        tests = [
            ("数据库下载", lambda: test_database_download(admin)),
            ("备份文件列表", lambda: test_backup_file_list(admin)),
        ]
        
        results = []
        backup_file = None
        
        for test_name, test_func in tests:
            print(f"\n🧪 测试 {test_name}...")
            try:
                result = test_func()
                if test_name == "数据库下载" and result:
                    backup_file = result
                    result = True
                
                results.append((test_name, result))
                if result:
                    print(f"✅ {test_name} 测试通过")
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"💥 {test_name} 测试异常: {e}")
                results.append((test_name, False))
        
        # 测试数据库上传准备
        print(f"\n🧪 测试数据库上传准备...")
        upload_result = test_database_upload(admin, backup_file)
        results.append(("数据库上传准备", upload_result))
        if upload_result:
            print(f"✅ 数据库上传准备 测试通过")
        else:
            print(f"❌ 数据库上传准备 测试失败")
        
        # 清理测试文件
        cleanup_test_files()
        
        print("\n" + "=" * 60)
        print("🎉 数据库备份和恢复功能测试完成！")
        
        print("\n📊 测试结果:")
        passed = 0
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n📈 总体结果: {passed}/{len(results)} 项测试通过")
        
        if passed == len(results):
            print("🎊 所有测试都通过了！数据库备份功能正常工作。")
            
            print("\n💡 使用说明:")
            print("1. 登录admin账号，进入系统设置")
            print("2. 在备份管理区域点击'下载数据库'")
            print("3. 数据库文件会自动下载到本地")
            print("4. 需要恢复时，选择.db文件并点击'恢复数据库'")
            print("5. 系统会自动验证文件并替换数据库")
            
            print("\n⚠️ 重要提醒:")
            print("• 数据库恢复会完全替换当前所有数据")
            print("• 建议在恢复前先下载当前数据库作为备份")
            print("• 恢复后建议刷新页面以加载新数据")
            
            return True
        else:
            print("⚠️ 部分测试失败，请检查相关功能。")
            return False
            
    except Exception as e:
        print(f"💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
