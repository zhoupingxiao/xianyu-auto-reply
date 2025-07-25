#!/usr/bin/env python3
"""
测试系统改进功能
"""

import requests
import time
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

def test_page_access():
    """测试页面访问"""
    logger.info("测试页面访问...")
    
    pages = [
        ("用户管理", "/user_management.html"),
        ("日志管理", "/log_management.html"),
        ("数据管理", "/data_management.html")
    ]
    
    results = []
    for page_name, page_url in pages:
        try:
            response = requests.get(f"{BASE_URL}{page_url}", timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✅ {page_name} 页面访问成功 (200)")
                results.append((page_name, True))
            else:
                logger.error(f"❌ {page_name} 页面访问失败 ({response.status_code})")
                results.append((page_name, False))
                
        except Exception as e:
            logger.error(f"❌ {page_name} 页面访问异常: {e}")
            results.append((page_name, False))
    
    return results

def test_data_management_api(admin):
    """测试数据管理API"""
    logger.info("测试数据管理API...")
    
    # 测试获取表数据
    tables_to_test = ['users', 'cookies', 'cards']
    
    for table in tables_to_test:
        try:
            response = requests.get(f"{BASE_URL}/admin/data/{table}", 
                                  headers=admin['headers'])
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    logger.info(f"✅ 获取 {table} 表数据成功，共 {data['count']} 条记录")
                else:
                    logger.error(f"❌ 获取 {table} 表数据失败: {data.get('message', '未知错误')}")
                    return False
            else:
                logger.error(f"❌ 获取 {table} 表数据失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 获取 {table} 表数据异常: {e}")
            return False
    
    return True

def test_log_management_api(admin):
    """测试日志管理API"""
    logger.info("测试日志管理API...")
    
    try:
        # 测试获取日志
        response = requests.get(f"{BASE_URL}/admin/logs?lines=10", 
                              headers=admin['headers'])
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            logger.info(f"✅ 获取系统日志成功，共 {len(logs)} 条")
            
            # 测试日志级别过滤
            response = requests.get(f"{BASE_URL}/admin/logs?lines=5&level=info", 
                                  headers=admin['headers'])
            
            if response.status_code == 200:
                data = response.json()
                info_logs = data.get('logs', [])
                logger.info(f"✅ INFO级别日志过滤成功，共 {len(info_logs)} 条")
                return True
            else:
                logger.error(f"❌ 日志级别过滤失败: {response.status_code}")
                return False
        else:
            logger.error(f"❌ 获取系统日志失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 日志管理API测试异常: {e}")
        return False

def test_database_backup_api(admin):
    """测试数据库备份API"""
    logger.info("测试数据库备份API...")
    
    try:
        # 测试数据库下载
        response = requests.get(f"{BASE_URL}/admin/backup/download", 
                              headers=admin['headers'])
        
        if response.status_code == 200:
            logger.info(f"✅ 数据库备份下载成功，文件大小: {len(response.content)} bytes")
            
            # 测试备份文件列表
            response = requests.get(f"{BASE_URL}/admin/backup/list", 
                                  headers=admin['headers'])
            
            if response.status_code == 200:
                data = response.json()
                backups = data.get('backups', [])
                logger.info(f"✅ 获取备份文件列表成功，共 {len(backups)} 个备份")
                return True
            else:
                logger.error(f"❌ 获取备份文件列表失败: {response.status_code}")
                return False
        else:
            logger.error(f"❌ 数据库备份下载失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 数据库备份API测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 系统改进功能测试")
    print("=" * 60)
    
    print("📋 测试内容:")
    print("• 页面访问测试")
    print("• 日志管理功能")
    print("• 数据管理功能")
    print("• 数据库备份功能")
    
    try:
        # 管理员登录
        admin = test_admin_login()
        if not admin:
            print("❌ 测试失败：管理员登录失败")
            return False
        
        print("✅ 管理员登录成功")
        
        # 测试页面访问
        print(f"\n🧪 测试页面访问...")
        page_results = test_page_access()
        
        page_success = all(result[1] for result in page_results)
        for page_name, success in page_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"   {page_name}: {status}")
        
        # 测试API功能
        tests = [
            ("数据管理API", lambda: test_data_management_api(admin)),
            ("日志管理API", lambda: test_log_management_api(admin)),
            ("数据库备份API", lambda: test_database_backup_api(admin)),
        ]
        
        api_results = []
        for test_name, test_func in tests:
            print(f"\n🧪 测试 {test_name}...")
            try:
                result = test_func()
                api_results.append((test_name, result))
                if result:
                    print(f"✅ {test_name} 测试通过")
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"💥 {test_name} 测试异常: {e}")
                api_results.append((test_name, False))
        
        print("\n" + "=" * 60)
        print("🎉 系统改进功能测试完成！")
        
        print("\n📊 测试结果:")
        
        # 页面访问结果
        print("页面访问:")
        for page_name, success in page_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {page_name}: {status}")
        
        # API功能结果
        print("API功能:")
        for test_name, success in api_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        # 总体结果
        all_results = page_results + api_results
        passed = sum(1 for _, success in all_results if success)
        total = len(all_results)
        
        print(f"\n📈 总体结果: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎊 所有测试都通过了！系统改进功能正常工作。")
            
            print("\n💡 功能说明:")
            print("1. 日志管理：最新日志显示在最上面")
            print("2. 系统设置：只保留数据库备份模式")
            print("3. 数据管理：新增管理员专用的数据表管理功能")
            print("4. 所有管理员功能都有严格的权限控制")
            
            print("\n🎯 使用方法:")
            print("• 使用admin账号登录系统")
            print("• 在侧边栏可以看到管理员功能菜单")
            print("• 点击相应功能进入管理页面")
            print("• 数据管理可以查看和删除表中的数据")
            
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
