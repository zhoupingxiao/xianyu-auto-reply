#!/usr/bin/env python3
"""
多用户系统迁移脚本
将历史数据绑定到admin用户，并创建admin用户记录
"""

import sqlite3
import hashlib
import time
from loguru import logger

def migrate_to_multiuser():
    """迁移到多用户系统"""
    print("🔄 开始迁移到多用户系统...")
    print("=" * 60)
    
    try:
        # 连接数据库
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        
        print("1️⃣ 检查数据库结构...")
        
        # 检查users表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_table_exists = cursor.fetchone() is not None
        
        if not users_table_exists:
            print("   ❌ users表不存在，请先运行主程序初始化数据库")
            return False
        
        print("   ✅ users表已存在")
        
        # 检查是否已有admin用户
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            admin_user_id = admin_user[0]
            print(f"   ✅ admin用户已存在，ID: {admin_user_id}")
        else:
            print("2️⃣ 创建admin用户...")
            
            # 获取当前的admin密码哈希
            cursor.execute("SELECT value FROM system_settings WHERE key = 'admin_password_hash'")
            password_hash_row = cursor.fetchone()
            
            if password_hash_row:
                admin_password_hash = password_hash_row[0]
            else:
                # 如果没有设置密码，使用默认密码 admin123
                admin_password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
                print("   ⚠️ 未找到admin密码，使用默认密码: admin123")
            
            # 创建admin用户
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin@localhost', admin_password_hash, True, time.time(), time.time()))
            
            admin_user_id = cursor.lastrowid
            print(f"   ✅ admin用户创建成功，ID: {admin_user_id}")
        
        print("3️⃣ 检查cookies表结构...")
        
        # 检查cookies表是否有user_id字段
        cursor.execute("PRAGMA table_info(cookies)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("   🔧 添加user_id字段到cookies表...")
            cursor.execute("ALTER TABLE cookies ADD COLUMN user_id INTEGER")
            print("   ✅ user_id字段添加成功")
        else:
            print("   ✅ user_id字段已存在")
        
        print("4️⃣ 迁移历史数据...")
        
        # 统计需要迁移的数据
        cursor.execute("SELECT COUNT(*) FROM cookies WHERE user_id IS NULL")
        cookies_to_migrate = cursor.fetchone()[0]
        
        if cookies_to_migrate > 0:
            print(f"   📊 发现 {cookies_to_migrate} 个cookies需要绑定到admin用户")
            
            # 将所有没有user_id的cookies绑定到admin用户
            cursor.execute("UPDATE cookies SET user_id = ? WHERE user_id IS NULL", (admin_user_id,))
            
            print(f"   ✅ 已将 {cookies_to_migrate} 个cookies绑定到admin用户")
        else:
            print("   ✅ 所有cookies已正确绑定用户")
        
        print("5️⃣ 验证迁移结果...")
        
        # 统计各用户的数据
        cursor.execute('''
        SELECT u.username, COUNT(c.id) as cookie_count
        FROM users u
        LEFT JOIN cookies c ON u.id = c.user_id
        GROUP BY u.id, u.username
        ''')
        
        user_stats = cursor.fetchall()
        print("   📊 用户数据统计:")
        for username, cookie_count in user_stats:
            print(f"     • {username}: {cookie_count} 个cookies")
        
        # 检查是否还有未绑定的数据
        cursor.execute("SELECT COUNT(*) FROM cookies WHERE user_id IS NULL")
        unbound_cookies = cursor.fetchone()[0]
        
        if unbound_cookies > 0:
            print(f"   ⚠️ 仍有 {unbound_cookies} 个cookies未绑定用户")
        else:
            print("   ✅ 所有cookies已正确绑定用户")
        
        # 提交事务
        conn.commit()
        print("\n6️⃣ 迁移完成！")
        
        print("\n" + "=" * 60)
        print("🎉 多用户系统迁移成功！")
        print("\n📋 迁移总结:")
        print(f"   • admin用户ID: {admin_user_id}")
        print(f"   • 迁移的cookies数量: {cookies_to_migrate}")
        print(f"   • 当前用户数量: {len(user_stats)}")
        
        print("\n💡 下一步操作:")
        print("   1. 重启应用程序")
        print("   2. 使用admin账号登录管理现有数据")
        print("   3. 其他用户可以通过注册页面创建新账号")
        print("   4. 每个用户只能看到自己的数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_migration_status():
    """检查迁移状态"""
    print("\n🔍 检查多用户系统状态...")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        
        # 检查users表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ users表不存在，需要先运行主程序初始化数据库")
            return
        
        # 检查用户数量
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"👥 用户数量: {user_count}")
        
        # 检查admin用户
        cursor.execute("SELECT id, username, email, is_active FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        if admin_user:
            print(f"👑 admin用户: ID={admin_user[0]}, 邮箱={admin_user[2]}, 状态={'激活' if admin_user[3] else '禁用'}")
        else:
            print("❌ admin用户不存在")
        
        # 检查cookies表结构
        cursor.execute("PRAGMA table_info(cookies)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'user_id' in columns:
            print("✅ cookies表已支持用户隔离")
            
            # 统计各用户的cookies
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
                print(f"\n⚠️ 发现 {unbound_count} 个未绑定用户的cookies，建议运行迁移")
            else:
                print("\n✅ 所有数据已正确绑定用户")
        else:
            print("❌ cookies表不支持用户隔离，需要运行迁移")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_migration_status()
    else:
        print("🚀 闲鱼自动回复系统 - 多用户迁移工具")
        print("=" * 60)
        print("此工具将帮助您将单用户系统迁移到多用户系统")
        print("主要功能:")
        print("• 创建admin用户账号")
        print("• 将历史数据绑定到admin用户")
        print("• 支持新用户注册和数据隔离")
        print("\n⚠️ 重要提醒:")
        print("• 迁移前请备份数据库文件")
        print("• 迁移过程中请勿操作系统")
        print("• 迁移完成后需要重启应用")
        
        confirm = input("\n是否继续迁移？(y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            success = migrate_to_multiuser()
            if success:
                print("\n🎊 迁移完成！请重启应用程序。")
            else:
                print("\n💥 迁移失败！请检查错误信息。")
        else:
            print("取消迁移。")
            
        print(f"\n💡 提示: 运行 'python {sys.argv[0]} check' 可以检查迁移状态")
