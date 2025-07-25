#!/usr/bin/env python3
"""
完整的多用户数据隔离修复脚本
"""

import sqlite3
import json
import time
from loguru import logger

def backup_database():
    """备份数据库"""
    try:
        import shutil
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = f"xianyu_data_backup_{timestamp}.db"
        shutil.copy2("xianyu_data.db", backup_file)
        logger.info(f"数据库备份完成: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        return None

def add_user_id_columns():
    """为相关表添加user_id字段"""
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    
    try:
        # 检查并添加user_id字段到cards表
        cursor.execute("PRAGMA table_info(cards)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            logger.info("为cards表添加user_id字段...")
            cursor.execute('ALTER TABLE cards ADD COLUMN user_id INTEGER REFERENCES users(id)')
            logger.info("✅ cards表user_id字段添加成功")
        else:
            logger.info("cards表已有user_id字段")
        
        # 检查并添加user_id字段到delivery_rules表
        cursor.execute("PRAGMA table_info(delivery_rules)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            logger.info("为delivery_rules表添加user_id字段...")
            cursor.execute('ALTER TABLE delivery_rules ADD COLUMN user_id INTEGER REFERENCES users(id)')
            logger.info("✅ delivery_rules表user_id字段添加成功")
        else:
            logger.info("delivery_rules表已有user_id字段")
        
        # 检查并添加user_id字段到notification_channels表
        cursor.execute("PRAGMA table_info(notification_channels)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            logger.info("为notification_channels表添加user_id字段...")
            cursor.execute('ALTER TABLE notification_channels ADD COLUMN user_id INTEGER REFERENCES users(id)')
            logger.info("✅ notification_channels表user_id字段添加成功")
        else:
            logger.info("notification_channels表已有user_id字段")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"添加user_id字段失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_user_settings_table():
    """创建用户设置表"""
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    
    try:
        # 检查表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        if cursor.fetchone():
            logger.info("user_settings表已存在")
            return True
        
        logger.info("创建user_settings表...")
        cursor.execute('''
        CREATE TABLE user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, key)
        )
        ''')
        
        conn.commit()
        logger.info("✅ user_settings表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"创建user_settings表失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_existing_data():
    """迁移现有数据到admin用户"""
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    
    try:
        # 获取admin用户ID
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_result = cursor.fetchone()
        
        if not admin_result:
            logger.error("未找到admin用户，请先创建admin用户")
            return False
        
        admin_id = admin_result[0]
        logger.info(f"找到admin用户，ID: {admin_id}")
        
        # 迁移cards表数据
        cursor.execute("SELECT COUNT(*) FROM cards WHERE user_id IS NULL")
        unbound_cards = cursor.fetchone()[0]
        
        if unbound_cards > 0:
            logger.info(f"迁移 {unbound_cards} 个未绑定的卡券到admin用户...")
            cursor.execute("UPDATE cards SET user_id = ? WHERE user_id IS NULL", (admin_id,))
            logger.info("✅ 卡券数据迁移完成")
        
        # 迁移delivery_rules表数据
        cursor.execute("SELECT COUNT(*) FROM delivery_rules WHERE user_id IS NULL")
        unbound_rules = cursor.fetchone()[0]
        
        if unbound_rules > 0:
            logger.info(f"迁移 {unbound_rules} 个未绑定的发货规则到admin用户...")
            cursor.execute("UPDATE delivery_rules SET user_id = ? WHERE user_id IS NULL", (admin_id,))
            logger.info("✅ 发货规则数据迁移完成")
        
        # 迁移notification_channels表数据
        cursor.execute("SELECT COUNT(*) FROM notification_channels WHERE user_id IS NULL")
        unbound_channels = cursor.fetchone()[0]
        
        if unbound_channels > 0:
            logger.info(f"迁移 {unbound_channels} 个未绑定的通知渠道到admin用户...")
            cursor.execute("UPDATE notification_channels SET user_id = ? WHERE user_id IS NULL", (admin_id,))
            logger.info("✅ 通知渠道数据迁移完成")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"数据迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_isolation():
    """验证数据隔离效果"""
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    
    try:
        logger.info("验证数据隔离效果...")
        
        # 检查各表的用户分布
        tables = ['cards', 'delivery_rules', 'notification_channels']
        
        for table in tables:
            cursor.execute(f'''
            SELECT u.username, COUNT(*) as count
            FROM {table} t
            JOIN users u ON t.user_id = u.id
            GROUP BY u.id, u.username
            ORDER BY count DESC
            ''')
            
            results = cursor.fetchall()
            logger.info(f"📊 {table} 表用户分布:")
            for username, count in results:
                logger.info(f"   • {username}: {count} 条记录")
            
            # 检查是否有未绑定的数据
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL")
            unbound_count = cursor.fetchone()[0]
            if unbound_count > 0:
                logger.warning(f"⚠️ {table} 表还有 {unbound_count} 条未绑定用户的记录")
            else:
                logger.info(f"✅ {table} 表所有记录都已正确绑定用户")
        
        return True
        
    except Exception as e:
        logger.error(f"验证失败: {e}")
        return False
    finally:
        conn.close()

def create_default_user_settings():
    """为现有用户创建默认设置"""
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    
    try:
        logger.info("为现有用户创建默认设置...")
        
        # 获取所有用户
        cursor.execute("SELECT id, username FROM users")
        users = cursor.fetchall()
        
        default_settings = [
            ('theme_color', '#1890ff', '主题颜色'),
            ('language', 'zh-CN', '界面语言'),
            ('notification_enabled', 'true', '通知开关'),
            ('auto_refresh', 'true', '自动刷新'),
        ]
        
        for user_id, username in users:
            logger.info(f"为用户 {username} 创建默认设置...")
            
            for key, value, description in default_settings:
                # 检查设置是否已存在
                cursor.execute(
                    "SELECT id FROM user_settings WHERE user_id = ? AND key = ?",
                    (user_id, key)
                )
                
                if not cursor.fetchone():
                    cursor.execute('''
                    INSERT INTO user_settings (user_id, key, value, description)
                    VALUES (?, ?, ?, ?)
                    ''', (user_id, key, value, description))
        
        conn.commit()
        logger.info("✅ 默认用户设置创建完成")
        return True
        
    except Exception as e:
        logger.error(f"创建默认用户设置失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("🚀 完整的多用户数据隔离修复")
    print("=" * 60)
    
    # 1. 备份数据库
    print("\n📦 1. 备份数据库")
    backup_file = backup_database()
    if not backup_file:
        print("❌ 数据库备份失败，停止修复")
        return False
    
    # 2. 添加user_id字段
    print("\n🔧 2. 添加用户隔离字段")
    if not add_user_id_columns():
        print("❌ 添加user_id字段失败")
        return False
    
    # 3. 创建用户设置表
    print("\n📋 3. 创建用户设置表")
    if not create_user_settings_table():
        print("❌ 创建用户设置表失败")
        return False
    
    # 4. 迁移现有数据
    print("\n📦 4. 迁移现有数据")
    if not migrate_existing_data():
        print("❌ 数据迁移失败")
        return False
    
    # 5. 创建默认用户设置
    print("\n⚙️ 5. 创建默认用户设置")
    if not create_default_user_settings():
        print("❌ 创建默认用户设置失败")
        return False
    
    # 6. 验证隔离效果
    print("\n🔍 6. 验证数据隔离")
    if not verify_isolation():
        print("❌ 验证失败")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 多用户数据隔离修复完成！")
    
    print("\n📋 修复内容:")
    print("✅ 1. 为cards表添加用户隔离")
    print("✅ 2. 为delivery_rules表添加用户隔离")
    print("✅ 3. 为notification_channels表添加用户隔离")
    print("✅ 4. 创建用户设置表")
    print("✅ 5. 迁移现有数据到admin用户")
    print("✅ 6. 创建默认用户设置")
    
    print("\n⚠️ 下一步:")
    print("1. 重启服务以应用数据库更改")
    print("2. 运行API接口修复脚本")
    print("3. 测试多用户数据隔离")
    print("4. 更新前端代码")
    
    print(f"\n💾 数据库备份文件: {backup_file}")
    print("如有问题，可以使用备份文件恢复数据")
    
    return True

if __name__ == "__main__":
    main()
