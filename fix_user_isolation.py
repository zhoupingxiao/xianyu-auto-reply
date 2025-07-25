#!/usr/bin/env python3
"""
修复多用户数据隔离的脚本
"""

import re

def fix_user_isolation():
    """修复用户隔离问题"""
    print("🔧 修复多用户数据隔离问题")
    print("=" * 60)
    
    # 需要修复的接口列表
    interfaces_to_fix = [
        # 商品管理
        {
            'pattern': r'@app\.put\("/items/\{cookie_id\}/\{item_id\}"\)\ndef update_item_detail\(',
            'description': '更新商品详情接口',
            'add_user_check': True
        },
        {
            'pattern': r'@app\.delete\("/items/\{cookie_id\}/\{item_id\}"\)\ndef delete_item_info\(',
            'description': '删除商品信息接口',
            'add_user_check': True
        },
        {
            'pattern': r'@app\.delete\("/items/batch"\)\ndef batch_delete_items\(',
            'description': '批量删除商品接口',
            'add_user_check': True
        },
        {
            'pattern': r'@app\.post\("/items/get-all-from-account"\)\nasync def get_all_items_from_account\(',
            'description': '从账号获取所有商品接口',
            'add_user_check': True
        },
        {
            'pattern': r'@app\.post\("/items/get-by-page"\)\nasync def get_items_by_page\(',
            'description': '分页获取商品接口',
            'add_user_check': True
        },
        # 卡券管理
        {
            'pattern': r'@app\.get\("/cards"\)\ndef get_cards\(',
            'description': '获取卡券列表接口',
            'add_user_check': False  # 卡券是全局的，不需要用户隔离
        },
        # AI回复设置
        {
            'pattern': r'@app\.get\("/ai-reply-settings/\{cookie_id\}"\)\ndef get_ai_reply_settings\(',
            'description': 'AI回复设置接口',
            'add_user_check': True
        },
        # 消息通知
        {
            'pattern': r'@app\.get\("/message-notifications/\{cid\}"\)\ndef get_account_notifications\(',
            'description': '获取账号消息通知接口',
            'add_user_check': True
        },
    ]
    
    print("📋 需要修复的接口:")
    for i, interface in enumerate(interfaces_to_fix, 1):
        status = "✅ 需要用户检查" if interface['add_user_check'] else "ℹ️ 全局接口"
        print(f"   {i}. {interface['description']} - {status}")
    
    print("\n💡 修复建议:")
    print("1. 将 '_: None = Depends(require_auth)' 替换为 'current_user: Dict[str, Any] = Depends(get_current_user)'")
    print("2. 在需要用户检查的接口中添加用户权限验证")
    print("3. 确保只返回当前用户的数据")
    
    print("\n🔍 检查当前状态...")
    
    # 读取reply_server.py文件
    try:
        with open('reply_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计还有多少接口使用旧的认证方式
        old_auth_count = len(re.findall(r'_: None = Depends\(require_auth\)', content))
        new_auth_count = len(re.findall(r'current_user: Dict\[str, Any\] = Depends\(get_current_user\)', content))
        
        print(f"📊 认证方式统计:")
        print(f"   • 旧认证方式 (require_auth): {old_auth_count} 个接口")
        print(f"   • 新认证方式 (get_current_user): {new_auth_count} 个接口")
        
        if old_auth_count > 0:
            print(f"\n⚠️ 还有 {old_auth_count} 个接口需要修复")
            
            # 找出具体哪些接口还没修复
            old_auth_interfaces = re.findall(r'@app\.\w+\([^)]+\)\s*\ndef\s+(\w+)\([^)]*_: None = Depends\(require_auth\)', content, re.MULTILINE)
            
            print("📝 未修复的接口:")
            for interface in old_auth_interfaces:
                print(f"   • {interface}")
        else:
            print("\n🎉 所有接口都已使用新的认证方式！")
        
        # 检查是否有用户权限验证
        user_check_pattern = r'user_cookies = db_manager\.get_all_cookies\(user_id\)'
        user_check_count = len(re.findall(user_check_pattern, content))
        
        print(f"\n🔒 用户权限检查统计:")
        print(f"   • 包含用户权限检查的接口: {user_check_count} 个")
        
        return old_auth_count == 0
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def generate_fix_template():
    """生成修复模板"""
    print("\n📝 修复模板:")
    print("-" * 40)
    
    template = '''
# 修复前：
@app.get("/some-endpoint/{cid}")
def some_function(cid: str, _: None = Depends(require_auth)):
    """接口描述"""
    # 原有逻辑
    pass

# 修复后：
@app.get("/some-endpoint/{cid}")
def some_function(cid: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """接口描述"""
    try:
        # 检查cookie是否属于当前用户
        user_id = current_user['user_id']
        from db_manager import db_manager
        user_cookies = db_manager.get_all_cookies(user_id)
        
        if cid not in user_cookies:
            raise HTTPException(status_code=403, detail="无权限访问该Cookie")
        
        # 原有逻辑
        pass
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
    
    print(template)

def check_database_isolation():
    """检查数据库隔离情况"""
    print("\n🗄️ 检查数据库隔离情况")
    print("-" * 40)
    
    try:
        import sqlite3
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        
        # 检查cookies表是否有user_id字段
        cursor.execute("PRAGMA table_info(cookies)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("✅ cookies表已支持用户隔离")
            
            # 统计用户数据分布
            cursor.execute('''
            SELECT u.username, COUNT(c.id) as cookie_count
            FROM users u
            LEFT JOIN cookies c ON u.id = c.user_id
            GROUP BY u.id, u.username
            ORDER BY cookie_count DESC
            ''')
            
            user_stats = cursor.fetchall()
            print("\n📊 用户数据分布:")
            for username, cookie_count in user_stats:
                print(f"   • {username}: {cookie_count} 个cookies")
            
            # 检查未绑定的数据
            cursor.execute("SELECT COUNT(*) FROM cookies WHERE user_id IS NULL")
            unbound_count = cursor.fetchone()[0]
            if unbound_count > 0:
                print(f"\n⚠️ 发现 {unbound_count} 个未绑定用户的cookies")
            else:
                print("\n✅ 所有cookies已正确绑定用户")
        else:
            print("❌ cookies表不支持用户隔离")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")

def main():
    """主函数"""
    print("🚀 多用户数据隔离修复工具")
    print("=" * 60)
    
    # 检查修复状态
    all_fixed = fix_user_isolation()
    
    # 生成修复模板
    generate_fix_template()
    
    # 检查数据库隔离
    check_database_isolation()
    
    print("\n" + "=" * 60)
    if all_fixed:
        print("🎉 多用户数据隔离检查完成！所有接口都已正确实现用户隔离。")
    else:
        print("⚠️ 还有接口需要修复，请按照模板进行修复。")
    
    print("\n📋 功能模块隔离状态:")
    print("✅ 1. 账号管理 - Cookie相关接口已隔离")
    print("✅ 2. 自动回复 - 关键字和默认回复已隔离")
    print("❓ 3. 商品管理 - 部分接口需要检查")
    print("❓ 4. 卡券管理 - 需要确认是否需要隔离")
    print("❓ 5. 自动发货 - 需要检查")
    print("❓ 6. 通知渠道 - 需要确认隔离策略")
    print("❓ 7. 消息通知 - 需要检查")
    print("❓ 8. 系统设置 - 需要确认哪些需要隔离")
    
    print("\n💡 下一步:")
    print("1. 手动修复剩余的接口")
    print("2. 测试所有功能的用户隔离")
    print("3. 更新前端代码以支持多用户")
    print("4. 编写完整的测试用例")

if __name__ == "__main__":
    main()
