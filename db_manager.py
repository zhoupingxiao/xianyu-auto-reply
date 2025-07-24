import sqlite3
import os
import threading
import hashlib
import time
import json
from typing import List, Tuple, Dict, Optional
from loguru import logger

class DBManager:
    """SQLite数据库管理，持久化存储Cookie和关键字"""
    
    def __init__(self, db_path: str = None):
        """初始化数据库连接和表结构"""
        # 支持环境变量配置数据库路径
        if db_path is None:
            db_path = os.getenv('DB_PATH', 'xianyu_data.db')

        # 确保数据目录存在并有正确权限
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, mode=0o755, exist_ok=True)
                logger.info(f"创建数据目录: {db_dir}")
            except PermissionError as e:
                logger.error(f"创建数据目录失败，权限不足: {e}")
                # 尝试使用当前目录
                db_path = os.path.basename(db_path)
                logger.warning(f"使用当前目录作为数据库路径: {db_path}")
            except Exception as e:
                logger.error(f"创建数据目录失败: {e}")
                raise

        # 检查目录权限
        if db_dir and os.path.exists(db_dir):
            if not os.access(db_dir, os.W_OK):
                logger.error(f"数据目录没有写权限: {db_dir}")
                # 尝试使用当前目录
                db_path = os.path.basename(db_path)
                logger.warning(f"使用当前目录作为数据库路径: {db_path}")

        self.db_path = db_path
        logger.info(f"数据库路径: {self.db_path}")
        self.conn = None
        self.lock = threading.RLock()  # 使用可重入锁保护数据库操作
        self.init_db()
    
    def init_db(self):
        """初始化数据库表结构"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            
            # 创建cookies表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cookies (
                id TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建keywords表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                cookie_id TEXT,
                keyword TEXT,
                reply TEXT,
                PRIMARY KEY (cookie_id, keyword),
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            # 创建cookie_status表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cookie_status (
                cookie_id TEXT PRIMARY KEY,
                enabled BOOLEAN DEFAULT TRUE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            # 创建AI回复配置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_reply_settings (
                cookie_id TEXT PRIMARY KEY,
                ai_enabled BOOLEAN DEFAULT FALSE,
                model_name TEXT DEFAULT 'qwen-plus',
                api_key TEXT,
                base_url TEXT DEFAULT 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                max_discount_percent INTEGER DEFAULT 10,
                max_discount_amount INTEGER DEFAULT 100,
                max_bargain_rounds INTEGER DEFAULT 3,
                custom_prompts TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            # 创建AI对话历史表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                bargain_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies (id) ON DELETE CASCADE
            )
            ''')

            # 创建AI商品信息缓存表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_item_cache (
                item_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                price REAL,
                description TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建卡券表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('api', 'text', 'data')),
                api_config TEXT,
                text_content TEXT,
                data_content TEXT,
                description TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建商品信息表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                item_title TEXT,
                item_description TEXT,
                item_category TEXT,
                item_price TEXT,
                item_detail TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE,
                UNIQUE(cookie_id, item_id)
            )
            ''')

            # 创建自动发货规则表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                card_id INTEGER NOT NULL,
                delivery_count INTEGER DEFAULT 1,
                enabled BOOLEAN DEFAULT TRUE,
                description TEXT,
                delivery_times INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
            )
            ''')

            # 创建默认回复表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS default_replies (
                cookie_id TEXT PRIMARY KEY,
                enabled BOOLEAN DEFAULT FALSE,
                reply_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            # 创建通知渠道表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('qq')),
                config TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建消息通知配置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE,
                FOREIGN KEY (channel_id) REFERENCES notification_channels(id) ON DELETE CASCADE,
                UNIQUE(cookie_id, channel_id)
            )
            ''')

            # 创建系统设置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 插入默认系统设置
            cursor.execute('''
            INSERT OR IGNORE INTO system_settings (key, value, description) VALUES
            ('admin_password_hash', ?, '管理员密码哈希'),
            ('theme_color', 'blue', '主题颜色')
            ''', (hashlib.sha256("admin123".encode()).hexdigest(),))

            self.conn.commit()
            logger.info(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            if self.conn:
                self.conn.close()
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def get_connection(self):
        """获取数据库连接，如果已关闭则重新连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self.conn
    
    # -------------------- Cookie操作 --------------------
    def save_cookie(self, cookie_id: str, cookie_value: str) -> bool:
        """保存Cookie到数据库，如存在则更新"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO cookies (id, value) VALUES (?, ?)",
                    (cookie_id, cookie_value)
                )
                self.conn.commit()
                logger.debug(f"Cookie保存成功: {cookie_id}")
                return True
            except Exception as e:
                logger.error(f"Cookie保存失败: {e}")
                self.conn.rollback()
                return False
    
    def delete_cookie(self, cookie_id: str) -> bool:
        """从数据库删除Cookie及其关键字"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                # 删除关联的关键字
                cursor.execute("DELETE FROM keywords WHERE cookie_id = ?", (cookie_id,))
                # 删除Cookie
                cursor.execute("DELETE FROM cookies WHERE id = ?", (cookie_id,))
                self.conn.commit()
                logger.debug(f"Cookie删除成功: {cookie_id}")
                return True
            except Exception as e:
                logger.error(f"Cookie删除失败: {e}")
                self.conn.rollback()
                return False
    
    def get_cookie(self, cookie_id: str) -> Optional[str]:
        """获取指定Cookie值"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT value FROM cookies WHERE id = ?", (cookie_id,))
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                logger.error(f"获取Cookie失败: {e}")
                return None
    
    def get_all_cookies(self) -> Dict[str, str]:
        """获取所有Cookie"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, value FROM cookies")
                return {row[0]: row[1] for row in cursor.fetchall()}
            except Exception as e:
                logger.error(f"获取所有Cookie失败: {e}")
                return {}

    def get_cookie_by_id(self, cookie_id: str) -> Optional[Dict[str, str]]:
        """根据ID获取Cookie信息

        Args:
            cookie_id: Cookie ID

        Returns:
            Dict包含cookie信息，包括cookies_str字段，如果不存在返回None
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, value, created_at FROM cookies WHERE id = ?", (cookie_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'cookies_str': result[1],  # 使用cookies_str字段名以匹配调用方期望
                        'value': result[1],        # 保持向后兼容
                        'created_at': result[2]
                    }
                return None
            except Exception as e:
                logger.error(f"根据ID获取Cookie失败: {e}")
                return None
    
    # -------------------- 关键字操作 --------------------
    def save_keywords(self, cookie_id: str, keywords: List[Tuple[str, str]]) -> bool:
        """保存关键字列表，先删除旧数据再插入新数据"""
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # 先删除该cookie_id的所有关键字
                cursor.execute("DELETE FROM keywords WHERE cookie_id = ?", (cookie_id,))

                # 插入新关键字
                for keyword, reply in keywords:
                    cursor.execute(
                        "INSERT INTO keywords (cookie_id, keyword, reply) VALUES (?, ?, ?)",
                        (cookie_id, keyword, reply)
                    )

                self.conn.commit()
                logger.info(f"关键字保存成功: {cookie_id}, {len(keywords)}条")
                return True
            except Exception as e:
                logger.error(f"关键字保存失败: {e}")
                self.conn.rollback()
                return False
    
    def get_keywords(self, cookie_id: str) -> List[Tuple[str, str]]:
        """获取指定Cookie的关键字列表"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT keyword, reply FROM keywords WHERE cookie_id = ?",
                    (cookie_id,)
                )
                return [(row[0], row[1]) for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"获取关键字失败: {e}")
                return []
    
    def get_all_keywords(self) -> Dict[str, List[Tuple[str, str]]]:
        """获取所有Cookie的关键字"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT cookie_id, keyword, reply FROM keywords")

                result = {}
                for row in cursor.fetchall():
                    cookie_id, keyword, reply = row
                    if cookie_id not in result:
                        result[cookie_id] = []
                    result[cookie_id].append((keyword, reply))

                return result
            except Exception as e:
                logger.error(f"获取所有关键字失败: {e}")
                return {}

    def save_cookie_status(self, cookie_id: str, enabled: bool):
        """保存Cookie的启用状态"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO cookie_status (cookie_id, enabled, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (cookie_id, enabled))
                self.conn.commit()
                logger.debug(f"保存Cookie状态: {cookie_id} -> {'启用' if enabled else '禁用'}")
            except Exception as e:
                logger.error(f"保存Cookie状态失败: {e}")
                raise

    def get_cookie_status(self, cookie_id: str) -> bool:
        """获取Cookie的启用状态"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT enabled FROM cookie_status WHERE cookie_id = ?', (cookie_id,))
                result = cursor.fetchone()
                return bool(result[0]) if result else True  # 默认启用
            except Exception as e:
                logger.error(f"获取Cookie状态失败: {e}")
                return True  # 出错时默认启用

    def get_all_cookie_status(self) -> Dict[str, bool]:
        """获取所有Cookie的启用状态"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT cookie_id, enabled FROM cookie_status')

                result = {}
                for row in cursor.fetchall():
                    cookie_id, enabled = row
                    result[cookie_id] = bool(enabled)

                return result
            except Exception as e:
                logger.error(f"获取所有Cookie状态失败: {e}")
                return {}

    # -------------------- AI回复设置操作 --------------------
    def save_ai_reply_settings(self, cookie_id: str, settings: dict) -> bool:
        """保存AI回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO ai_reply_settings
                (cookie_id, ai_enabled, model_name, api_key, base_url,
                 max_discount_percent, max_discount_amount, max_bargain_rounds,
                 custom_prompts, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    cookie_id,
                    settings.get('ai_enabled', False),
                    settings.get('model_name', 'qwen-plus'),
                    settings.get('api_key', ''),
                    settings.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
                    settings.get('max_discount_percent', 10),
                    settings.get('max_discount_amount', 100),
                    settings.get('max_bargain_rounds', 3),
                    settings.get('custom_prompts', '')
                ))
                self.conn.commit()
                logger.debug(f"AI回复设置保存成功: {cookie_id}")
                return True
            except Exception as e:
                logger.error(f"保存AI回复设置失败: {e}")
                self.conn.rollback()
                return False

    def get_ai_reply_settings(self, cookie_id: str) -> dict:
        """获取AI回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT ai_enabled, model_name, api_key, base_url,
                       max_discount_percent, max_discount_amount, max_bargain_rounds,
                       custom_prompts
                FROM ai_reply_settings WHERE cookie_id = ?
                ''', (cookie_id,))

                result = cursor.fetchone()
                if result:
                    return {
                        'ai_enabled': bool(result[0]),
                        'model_name': result[1],
                        'api_key': result[2],
                        'base_url': result[3],
                        'max_discount_percent': result[4],
                        'max_discount_amount': result[5],
                        'max_bargain_rounds': result[6],
                        'custom_prompts': result[7]
                    }
                else:
                    # 返回默认设置
                    return {
                        'ai_enabled': False,
                        'model_name': 'qwen-plus',
                        'api_key': '',
                        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                        'max_discount_percent': 10,
                        'max_discount_amount': 100,
                        'max_bargain_rounds': 3,
                        'custom_prompts': ''
                    }
            except Exception as e:
                logger.error(f"获取AI回复设置失败: {e}")
                return {
                    'ai_enabled': False,
                    'model_name': 'qwen-plus',
                    'api_key': '',
                    'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                    'max_discount_percent': 10,
                    'max_discount_amount': 100,
                    'max_bargain_rounds': 3,
                    'custom_prompts': ''
                }

    def get_all_ai_reply_settings(self) -> Dict[str, dict]:
        """获取所有账号的AI回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT cookie_id, ai_enabled, model_name, api_key, base_url,
                       max_discount_percent, max_discount_amount, max_bargain_rounds,
                       custom_prompts
                FROM ai_reply_settings
                ''')

                result = {}
                for row in cursor.fetchall():
                    cookie_id = row[0]
                    result[cookie_id] = {
                        'ai_enabled': bool(row[1]),
                        'model_name': row[2],
                        'api_key': row[3],
                        'base_url': row[4],
                        'max_discount_percent': row[5],
                        'max_discount_amount': row[6],
                        'max_bargain_rounds': row[7],
                        'custom_prompts': row[8]
                    }

                return result
            except Exception as e:
                logger.error(f"获取所有AI回复设置失败: {e}")
                return {}

    # -------------------- 默认回复操作 --------------------
    def save_default_reply(self, cookie_id: str, enabled: bool, reply_content: str = None):
        """保存默认回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO default_replies (cookie_id, enabled, reply_content, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (cookie_id, enabled, reply_content))
                self.conn.commit()
                logger.debug(f"保存默认回复设置: {cookie_id} -> {'启用' if enabled else '禁用'}")
            except Exception as e:
                logger.error(f"保存默认回复设置失败: {e}")
                raise

    def get_default_reply(self, cookie_id: str) -> Optional[Dict[str, any]]:
        """获取指定账号的默认回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT enabled, reply_content FROM default_replies WHERE cookie_id = ?
                ''', (cookie_id,))
                result = cursor.fetchone()
                if result:
                    enabled, reply_content = result
                    return {
                        'enabled': bool(enabled),
                        'reply_content': reply_content or ''
                    }
                return None
            except Exception as e:
                logger.error(f"获取默认回复设置失败: {e}")
                return None

    def get_all_default_replies(self) -> Dict[str, Dict[str, any]]:
        """获取所有账号的默认回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT cookie_id, enabled, reply_content FROM default_replies')

                result = {}
                for row in cursor.fetchall():
                    cookie_id, enabled, reply_content = row
                    result[cookie_id] = {
                        'enabled': bool(enabled),
                        'reply_content': reply_content or ''
                    }

                return result
            except Exception as e:
                logger.error(f"获取所有默认回复设置失败: {e}")
                return {}

    def delete_default_reply(self, cookie_id: str) -> bool:
        """删除指定账号的默认回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM default_replies WHERE cookie_id = ?", (cookie_id,))
                self.conn.commit()
                logger.debug(f"删除默认回复设置: {cookie_id}")
                return True
            except Exception as e:
                logger.error(f"删除默认回复设置失败: {e}")
                self.conn.rollback()
                return False

    # -------------------- 通知渠道操作 --------------------
    def create_notification_channel(self, name: str, channel_type: str, config: str) -> int:
        """创建通知渠道"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT INTO notification_channels (name, type, config)
                VALUES (?, ?, ?)
                ''', (name, channel_type, config))
                self.conn.commit()
                channel_id = cursor.lastrowid
                logger.debug(f"创建通知渠道: {name} (ID: {channel_id})")
                return channel_id
            except Exception as e:
                logger.error(f"创建通知渠道失败: {e}")
                self.conn.rollback()
                raise

    def get_notification_channels(self) -> List[Dict[str, any]]:
        """获取所有通知渠道"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT id, name, type, config, enabled, created_at, updated_at
                FROM notification_channels
                ORDER BY created_at DESC
                ''')

                channels = []
                for row in cursor.fetchall():
                    channels.append({
                        'id': row[0],
                        'name': row[1],
                        'type': row[2],
                        'config': row[3],
                        'enabled': bool(row[4]),
                        'created_at': row[5],
                        'updated_at': row[6]
                    })

                return channels
            except Exception as e:
                logger.error(f"获取通知渠道失败: {e}")
                return []

    def get_notification_channel(self, channel_id: int) -> Optional[Dict[str, any]]:
        """获取指定通知渠道"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT id, name, type, config, enabled, created_at, updated_at
                FROM notification_channels WHERE id = ?
                ''', (channel_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'type': row[2],
                        'config': row[3],
                        'enabled': bool(row[4]),
                        'created_at': row[5],
                        'updated_at': row[6]
                    }
                return None
            except Exception as e:
                logger.error(f"获取通知渠道失败: {e}")
                return None

    def update_notification_channel(self, channel_id: int, name: str, config: str, enabled: bool = True) -> bool:
        """更新通知渠道"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                UPDATE notification_channels
                SET name = ?, config = ?, enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (name, config, enabled, channel_id))
                self.conn.commit()
                logger.debug(f"更新通知渠道: {channel_id}")
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"更新通知渠道失败: {e}")
                self.conn.rollback()
                return False

    def delete_notification_channel(self, channel_id: int) -> bool:
        """删除通知渠道"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM notification_channels WHERE id = ?", (channel_id,))
                self.conn.commit()
                logger.debug(f"删除通知渠道: {channel_id}")
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"删除通知渠道失败: {e}")
                self.conn.rollback()
                return False

    # -------------------- 消息通知配置操作 --------------------
    def set_message_notification(self, cookie_id: str, channel_id: int, enabled: bool = True) -> bool:
        """设置账号的消息通知"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO message_notifications (cookie_id, channel_id, enabled)
                VALUES (?, ?, ?)
                ''', (cookie_id, channel_id, enabled))
                self.conn.commit()
                logger.debug(f"设置消息通知: {cookie_id} -> {channel_id}")
                return True
            except Exception as e:
                logger.error(f"设置消息通知失败: {e}")
                self.conn.rollback()
                return False

    def get_account_notifications(self, cookie_id: str) -> List[Dict[str, any]]:
        """获取账号的通知配置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT mn.id, mn.channel_id, mn.enabled, nc.name, nc.type, nc.config
                FROM message_notifications mn
                JOIN notification_channels nc ON mn.channel_id = nc.id
                WHERE mn.cookie_id = ? AND nc.enabled = 1
                ORDER BY mn.id
                ''', (cookie_id,))

                notifications = []
                for row in cursor.fetchall():
                    notifications.append({
                        'id': row[0],
                        'channel_id': row[1],
                        'enabled': bool(row[2]),
                        'channel_name': row[3],
                        'channel_type': row[4],
                        'channel_config': row[5]
                    })

                return notifications
            except Exception as e:
                logger.error(f"获取账号通知配置失败: {e}")
                return []

    def get_all_message_notifications(self) -> Dict[str, List[Dict[str, any]]]:
        """获取所有账号的通知配置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT mn.cookie_id, mn.id, mn.channel_id, mn.enabled, nc.name, nc.type, nc.config
                FROM message_notifications mn
                JOIN notification_channels nc ON mn.channel_id = nc.id
                WHERE nc.enabled = 1
                ORDER BY mn.cookie_id, mn.id
                ''')

                result = {}
                for row in cursor.fetchall():
                    cookie_id = row[0]
                    if cookie_id not in result:
                        result[cookie_id] = []

                    result[cookie_id].append({
                        'id': row[1],
                        'channel_id': row[2],
                        'enabled': bool(row[3]),
                        'channel_name': row[4],
                        'channel_type': row[5],
                        'channel_config': row[6]
                    })

                return result
            except Exception as e:
                logger.error(f"获取所有消息通知配置失败: {e}")
                return {}

    def delete_message_notification(self, notification_id: int) -> bool:
        """删除消息通知配置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM message_notifications WHERE id = ?", (notification_id,))
                self.conn.commit()
                logger.debug(f"删除消息通知配置: {notification_id}")
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"删除消息通知配置失败: {e}")
                self.conn.rollback()
                return False

    def delete_account_notifications(self, cookie_id: str) -> bool:
        """删除账号的所有消息通知配置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM message_notifications WHERE cookie_id = ?", (cookie_id,))
                self.conn.commit()
                logger.debug(f"删除账号通知配置: {cookie_id}")
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"删除账号通知配置失败: {e}")
                self.conn.rollback()
                return False

    # -------------------- 备份和恢复操作 --------------------
    def export_backup(self) -> Dict[str, any]:
        """导出系统备份数据"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                backup_data = {
                    'version': '1.0',
                    'timestamp': time.time(),
                    'data': {}
                }

                # 备份所有表的数据
                tables = [
                    'cookies', 'keywords', 'cookie_status', 'cards',
                    'delivery_rules', 'default_replies', 'notification_channels',
                    'message_notifications', 'system_settings', 'item_info',
                    'ai_reply_settings', 'ai_conversations', 'ai_item_cache'
                ]

                for table in tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()

                    backup_data['data'][table] = {
                        'columns': columns,
                        'rows': [list(row) for row in rows]
                    }

                logger.info(f"导出备份成功，包含 {len(tables)} 个表")
                return backup_data

            except Exception as e:
                logger.error(f"导出备份失败: {e}")
                raise

    def import_backup(self, backup_data: Dict[str, any]) -> bool:
        """导入系统备份数据"""
        with self.lock:
            try:
                # 验证备份数据格式
                if not isinstance(backup_data, dict) or 'data' not in backup_data:
                    raise ValueError("备份数据格式无效")

                # 开始事务
                cursor = self.conn.cursor()
                cursor.execute("BEGIN TRANSACTION")

                # 清空现有数据（除了管理员密码）
                # 注意：按照外键依赖关系的逆序删除
                tables = [
                    'message_notifications', 'notification_channels', 'default_replies',
                    'delivery_rules', 'cards', 'item_info', 'cookie_status', 'keywords',
                    'ai_conversations', 'ai_reply_settings', 'ai_item_cache', 'cookies'
                ]

                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")

                # 清空系统设置（保留管理员密码）
                cursor.execute("DELETE FROM system_settings WHERE key != 'admin_password_hash'")

                # 导入数据
                data = backup_data['data']
                for table_name, table_data in data.items():
                    if table_name not in ['cookies', 'keywords', 'cookie_status', 'cards',
                                        'delivery_rules', 'default_replies', 'notification_channels',
                                        'message_notifications', 'system_settings', 'item_info',
                                        'ai_reply_settings', 'ai_conversations', 'ai_item_cache']:
                        continue

                    columns = table_data['columns']
                    rows = table_data['rows']

                    if not rows:
                        continue

                    # 构建插入语句
                    placeholders = ','.join(['?' for _ in columns])

                    if table_name == 'system_settings':
                        # 系统设置需要特殊处理，避免覆盖管理员密码
                        for row in rows:
                            if len(row) >= 1 and row[0] != 'admin_password_hash':
                                cursor.execute(f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})", row)
                    else:
                        cursor.executemany(f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})", rows)

                # 提交事务
                self.conn.commit()
                logger.info("导入备份成功")
                return True

            except Exception as e:
                logger.error(f"导入备份失败: {e}")
                self.conn.rollback()
                return False

    # -------------------- 系统设置操作 --------------------
    def get_system_setting(self, key: str) -> Optional[str]:
        """获取系统设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                logger.error(f"获取系统设置失败: {e}")
                return None

    def set_system_setting(self, key: str, value: str, description: str = None) -> bool:
        """设置系统设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO system_settings (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (key, value, description))
                self.conn.commit()
                logger.debug(f"设置系统设置: {key}")
                return True
            except Exception as e:
                logger.error(f"设置系统设置失败: {e}")
                self.conn.rollback()
                return False

    def get_all_system_settings(self) -> Dict[str, str]:
        """获取所有系统设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT key, value FROM system_settings")

                settings = {}
                for row in cursor.fetchall():
                    settings[row[0]] = row[1]

                return settings
            except Exception as e:
                logger.error(f"获取所有系统设置失败: {e}")
                return {}

    def verify_admin_password(self, password: str) -> bool:
        """验证管理员密码"""
        stored_hash = self.get_system_setting('admin_password_hash')
        if not stored_hash:
            return False

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == stored_hash

    def update_admin_password(self, new_password: str) -> bool:
        """更新管理员密码"""
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        return self.set_system_setting('admin_password_hash', password_hash, '管理员密码哈希')

    # ==================== 卡券管理方法 ====================

    def create_card(self, name: str, card_type: str, api_config=None,
                   text_content: str = None, data_content: str = None,
                   description: str = None, enabled: bool = True):
        """创建新卡券"""
        with self.lock:
            try:
                # 处理api_config参数 - 如果是字典则转换为JSON字符串
                api_config_str = None
                if api_config is not None:
                    if isinstance(api_config, dict):
                        import json
                        api_config_str = json.dumps(api_config)
                    else:
                        api_config_str = str(api_config)

                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT INTO cards (name, type, api_config, text_content, data_content,
                                 description, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, card_type, api_config_str, text_content, data_content,
                      description, enabled))
                self.conn.commit()
                card_id = cursor.lastrowid
                logger.info(f"创建卡券成功: {name} (ID: {card_id})")
                return card_id
            except Exception as e:
                logger.error(f"创建卡券失败: {e}")
                raise

    def get_all_cards(self):
        """获取所有卡券"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT id, name, type, api_config, text_content, data_content,
                       description, enabled, created_at, updated_at
                FROM cards
                ORDER BY created_at DESC
                ''')

                cards = []
                for row in cursor.fetchall():
                    # 解析api_config JSON字符串
                    api_config = row[3]
                    if api_config:
                        try:
                            import json
                            api_config = json.loads(api_config)
                        except (json.JSONDecodeError, TypeError):
                            # 如果解析失败，保持原始字符串
                            pass

                    cards.append({
                        'id': row[0],
                        'name': row[1],
                        'type': row[2],
                        'api_config': api_config,
                        'text_content': row[4],
                        'data_content': row[5],
                        'description': row[6],
                        'enabled': bool(row[7]),
                        'created_at': row[8],
                        'updated_at': row[9]
                    })

                return cards
            except Exception as e:
                logger.error(f"获取卡券列表失败: {e}")
                return []

    def get_card_by_id(self, card_id: int):
        """根据ID获取卡券"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT id, name, type, api_config, text_content, data_content,
                       description, enabled, created_at, updated_at
                FROM cards WHERE id = ?
                ''', (card_id,))

                row = cursor.fetchone()
                if row:
                    # 解析api_config JSON字符串
                    api_config = row[3]
                    if api_config:
                        try:
                            import json
                            api_config = json.loads(api_config)
                        except (json.JSONDecodeError, TypeError):
                            # 如果解析失败，保持原始字符串
                            pass

                    return {
                        'id': row[0],
                        'name': row[1],
                        'type': row[2],
                        'api_config': api_config,
                        'text_content': row[4],
                        'data_content': row[5],
                        'description': row[6],
                        'enabled': bool(row[7]),
                        'created_at': row[8],
                        'updated_at': row[9]
                    }
                return None
            except Exception as e:
                logger.error(f"获取卡券失败: {e}")
                return None

    def update_card(self, card_id: int, name: str = None, card_type: str = None,
                   api_config=None, text_content: str = None, data_content: str = None,
                   description: str = None, enabled: bool = None):
        """更新卡券"""
        with self.lock:
            try:
                # 处理api_config参数
                api_config_str = None
                if api_config is not None:
                    if isinstance(api_config, dict):
                        import json
                        api_config_str = json.dumps(api_config)
                    else:
                        api_config_str = str(api_config)

                cursor = self.conn.cursor()

                # 构建更新语句
                update_fields = []
                params = []

                if name is not None:
                    update_fields.append("name = ?")
                    params.append(name)
                if card_type is not None:
                    update_fields.append("type = ?")
                    params.append(card_type)
                if api_config_str is not None:
                    update_fields.append("api_config = ?")
                    params.append(api_config_str)
                if text_content is not None:
                    update_fields.append("text_content = ?")
                    params.append(text_content)
                if data_content is not None:
                    update_fields.append("data_content = ?")
                    params.append(data_content)
                if description is not None:
                    update_fields.append("description = ?")
                    params.append(description)
                if enabled is not None:
                    update_fields.append("enabled = ?")
                    params.append(enabled)

                if not update_fields:
                    return True  # 没有需要更新的字段

                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(card_id)

                sql = f"UPDATE cards SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(sql, params)

                if cursor.rowcount > 0:
                    self.conn.commit()
                    logger.info(f"更新卡券成功: ID {card_id}")
                    return True
                else:
                    return False  # 没有找到对应的记录

            except Exception as e:
                logger.error(f"更新卡券失败: {e}")
                self.conn.rollback()
                raise

    # ==================== 自动发货规则方法 ====================

    def create_delivery_rule(self, keyword: str, card_id: int, delivery_count: int = 1,
                           enabled: bool = True, description: str = None):
        """创建发货规则"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT INTO delivery_rules (keyword, card_id, delivery_count, enabled, description)
                VALUES (?, ?, ?, ?, ?)
                ''', (keyword, card_id, delivery_count, enabled, description))
                self.conn.commit()
                rule_id = cursor.lastrowid
                logger.info(f"创建发货规则成功: {keyword} -> 卡券ID {card_id} (规则ID: {rule_id})")
                return rule_id
            except Exception as e:
                logger.error(f"创建发货规则失败: {e}")
                raise

    def get_all_delivery_rules(self):
        """获取所有发货规则"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT dr.id, dr.keyword, dr.card_id, dr.delivery_count, dr.enabled,
                       dr.description, dr.delivery_times, dr.created_at, dr.updated_at,
                       c.name as card_name, c.type as card_type
                FROM delivery_rules dr
                LEFT JOIN cards c ON dr.card_id = c.id
                ORDER BY dr.created_at DESC
                ''')

                rules = []
                for row in cursor.fetchall():
                    rules.append({
                        'id': row[0],
                        'keyword': row[1],
                        'card_id': row[2],
                        'delivery_count': row[3],
                        'enabled': bool(row[4]),
                        'description': row[5],
                        'delivery_times': row[6],
                        'created_at': row[7],
                        'updated_at': row[8],
                        'card_name': row[9],
                        'card_type': row[10]
                    })

                return rules
            except Exception as e:
                logger.error(f"获取发货规则列表失败: {e}")
                return []

    def get_delivery_rules_by_keyword(self, keyword: str):
        """根据关键字获取匹配的发货规则"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                # 使用更灵活的匹配方式：既支持商品内容包含关键字，也支持关键字包含在商品内容中
                cursor.execute('''
                SELECT dr.id, dr.keyword, dr.card_id, dr.delivery_count, dr.enabled,
                       dr.description, dr.delivery_times,
                       c.name as card_name, c.type as card_type, c.api_config,
                       c.text_content, c.data_content, c.enabled as card_enabled
                FROM delivery_rules dr
                LEFT JOIN cards c ON dr.card_id = c.id
                WHERE dr.enabled = 1 AND c.enabled = 1
                AND (? LIKE '%' || dr.keyword || '%' OR dr.keyword LIKE '%' || ? || '%')
                ORDER BY
                    CASE
                        WHEN ? LIKE '%' || dr.keyword || '%' THEN LENGTH(dr.keyword)
                        ELSE LENGTH(dr.keyword) / 2
                    END DESC,
                    dr.id ASC
                ''', (keyword, keyword, keyword))

                rules = []
                for row in cursor.fetchall():
                    # 解析api_config JSON字符串
                    api_config = row[9]
                    if api_config:
                        try:
                            import json
                            api_config = json.loads(api_config)
                        except (json.JSONDecodeError, TypeError):
                            # 如果解析失败，保持原始字符串
                            pass

                    rules.append({
                        'id': row[0],
                        'keyword': row[1],
                        'card_id': row[2],
                        'delivery_count': row[3],
                        'enabled': bool(row[4]),
                        'description': row[5],
                        'delivery_times': row[6],
                        'card_name': row[7],
                        'card_type': row[8],
                        'card_api_config': api_config,
                        'card_text_content': row[10],
                        'card_data_content': row[11],
                        'card_enabled': bool(row[12])
                    })

                return rules
            except Exception as e:
                logger.error(f"根据关键字获取发货规则失败: {e}")
                return []

    def get_delivery_rule_by_id(self, rule_id: int):
        """根据ID获取发货规则"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT dr.id, dr.keyword, dr.card_id, dr.delivery_count, dr.enabled,
                       dr.description, dr.delivery_times, dr.created_at, dr.updated_at,
                       c.name as card_name, c.type as card_type
                FROM delivery_rules dr
                LEFT JOIN cards c ON dr.card_id = c.id
                WHERE dr.id = ?
                ''', (rule_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'keyword': row[1],
                        'card_id': row[2],
                        'delivery_count': row[3],
                        'enabled': bool(row[4]),
                        'description': row[5],
                        'delivery_times': row[6],
                        'created_at': row[7],
                        'updated_at': row[8],
                        'card_name': row[9],
                        'card_type': row[10]
                    }
                return None
            except Exception as e:
                logger.error(f"获取发货规则失败: {e}")
                return None

    def update_delivery_rule(self, rule_id: int, keyword: str = None, card_id: int = None,
                           delivery_count: int = None, enabled: bool = None,
                           description: str = None):
        """更新发货规则"""
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # 构建更新语句
                update_fields = []
                params = []

                if keyword is not None:
                    update_fields.append("keyword = ?")
                    params.append(keyword)
                if card_id is not None:
                    update_fields.append("card_id = ?")
                    params.append(card_id)
                if delivery_count is not None:
                    update_fields.append("delivery_count = ?")
                    params.append(delivery_count)
                if enabled is not None:
                    update_fields.append("enabled = ?")
                    params.append(enabled)
                if description is not None:
                    update_fields.append("description = ?")
                    params.append(description)

                if not update_fields:
                    return True  # 没有需要更新的字段

                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(rule_id)

                sql = f"UPDATE delivery_rules SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(sql, params)

                if cursor.rowcount > 0:
                    self.conn.commit()
                    logger.info(f"更新发货规则成功: ID {rule_id}")
                    return True
                else:
                    return False  # 没有找到对应的记录

            except Exception as e:
                logger.error(f"更新发货规则失败: {e}")
                self.conn.rollback()
                raise

    def increment_delivery_times(self, rule_id: int):
        """增加发货次数"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                UPDATE delivery_rules
                SET delivery_times = delivery_times + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (rule_id,))
                self.conn.commit()
                logger.debug(f"发货规则 {rule_id} 发货次数已增加")
            except Exception as e:
                logger.error(f"更新发货次数失败: {e}")

    def delete_card(self, card_id: int):
        """删除卡券"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))

                if cursor.rowcount > 0:
                    self.conn.commit()
                    logger.info(f"删除卡券成功: ID {card_id}")
                    return True
                else:
                    return False  # 没有找到对应的记录

            except Exception as e:
                logger.error(f"删除卡券失败: {e}")
                self.conn.rollback()
                raise

    def delete_delivery_rule(self, rule_id: int):
        """删除发货规则"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM delivery_rules WHERE id = ?", (rule_id,))

                if cursor.rowcount > 0:
                    self.conn.commit()
                    logger.info(f"删除发货规则成功: ID {rule_id}")
                    return True
                else:
                    return False  # 没有找到对应的记录

            except Exception as e:
                logger.error(f"删除发货规则失败: {e}")
                self.conn.rollback()
                raise

    def consume_batch_data(self, card_id: int):
        """消费批量数据的第一条记录（线程安全）"""
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # 获取卡券的批量数据
                cursor.execute("SELECT data_content FROM cards WHERE id = ? AND type = 'data'", (card_id,))
                result = cursor.fetchone()

                if not result or not result[0]:
                    logger.warning(f"卡券 {card_id} 没有批量数据")
                    return None

                data_content = result[0]
                lines = [line.strip() for line in data_content.split('\n') if line.strip()]

                if not lines:
                    logger.warning(f"卡券 {card_id} 批量数据为空")
                    return None

                # 获取第一条数据
                first_line = lines[0]

                # 移除第一条数据，更新数据库
                remaining_lines = lines[1:]
                new_data_content = '\n'.join(remaining_lines)

                cursor.execute('''
                UPDATE cards
                SET data_content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (new_data_content, card_id))

                self.conn.commit()

                logger.info(f"消费批量数据成功: 卡券ID={card_id}, 剩余={len(remaining_lines)}条")
                return first_line

            except Exception as e:
                logger.error(f"消费批量数据失败: {e}")
                self.conn.rollback()
                return None

    # ==================== 商品信息管理 ====================

    def save_item_basic_info(self, cookie_id: str, item_id: str, item_title: str = None,
                            item_description: str = None, item_category: str = None,
                            item_price: str = None, item_detail: str = None) -> bool:
        """保存或更新商品基本信息，使用原子操作避免并发问题

        Args:
            cookie_id: Cookie ID
            item_id: 商品ID
            item_title: 商品标题
            item_description: 商品描述
            item_category: 商品分类
            item_price: 商品价格
            item_detail: 商品详情JSON

        Returns:
            bool: 操作是否成功
        """
        try:
            with self.lock:
                cursor = self.conn.cursor()

                # 使用 INSERT OR IGNORE + UPDATE 的原子操作模式
                # 首先尝试插入，如果已存在则忽略
                cursor.execute('''
                INSERT OR IGNORE INTO item_info (cookie_id, item_id, item_title, item_description,
                                               item_category, item_price, item_detail, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (cookie_id, item_id, item_title or '', item_description or '',
                      item_category or '', item_price or '', item_detail or ''))

                # 如果是新插入的记录，直接返回成功
                if cursor.rowcount > 0:
                    self.conn.commit()
                    logger.info(f"新增商品基本信息: {item_id} - {item_title}")
                    return True

                # 记录已存在，使用原子UPDATE操作，只更新非空字段且不覆盖现有非空值
                update_parts = []
                params = []

                # 使用 CASE WHEN 语句进行条件更新，避免覆盖现有数据
                if item_title:
                    update_parts.append("item_title = CASE WHEN (item_title IS NULL OR item_title = '') THEN ? ELSE item_title END")
                    params.append(item_title)

                if item_description:
                    update_parts.append("item_description = CASE WHEN (item_description IS NULL OR item_description = '') THEN ? ELSE item_description END")
                    params.append(item_description)

                if item_category:
                    update_parts.append("item_category = CASE WHEN (item_category IS NULL OR item_category = '') THEN ? ELSE item_category END")
                    params.append(item_category)

                if item_price:
                    update_parts.append("item_price = CASE WHEN (item_price IS NULL OR item_price = '') THEN ? ELSE item_price END")
                    params.append(item_price)

                # 对于item_detail，只有在现有值为空时才更新
                if item_detail:
                    update_parts.append("item_detail = CASE WHEN (item_detail IS NULL OR item_detail = '' OR TRIM(item_detail) = '') THEN ? ELSE item_detail END")
                    params.append(item_detail)

                if update_parts:
                    update_parts.append("updated_at = CURRENT_TIMESTAMP")
                    params.extend([cookie_id, item_id])

                    sql = f"UPDATE item_info SET {', '.join(update_parts)} WHERE cookie_id = ? AND item_id = ?"
                    cursor.execute(sql, params)

                    if cursor.rowcount > 0:
                        logger.info(f"更新商品基本信息: {item_id} - {item_title}")
                    else:
                        logger.debug(f"商品信息无需更新: {item_id}")

                self.conn.commit()
                return True

        except Exception as e:
            logger.error(f"保存商品基本信息失败: {e}")
            self.conn.rollback()
            return False

    def save_item_info(self, cookie_id: str, item_id: str, item_data = None) -> bool:
        """保存或更新商品信息

        Args:
            cookie_id: Cookie ID
            item_id: 商品ID
            item_data: 商品详情数据，可以是字符串或字典，也可以为None

        Returns:
            bool: 操作是否成功
        """
        try:
            with self.lock:
                cursor = self.conn.cursor()

                # 检查商品是否已存在
                cursor.execute('''
                SELECT id, item_detail FROM item_info
                WHERE cookie_id = ? AND item_id = ?
                ''', (cookie_id, item_id))

                existing = cursor.fetchone()

                if existing:
                    # 如果传入的商品详情有值，则用最新数据覆盖
                    if item_data is not None and item_data:
                        # 处理字符串类型的详情数据
                        if isinstance(item_data, str):
                            cursor.execute('''
                            UPDATE item_info SET
                                item_detail = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE cookie_id = ? AND item_id = ?
                            ''', (item_data, cookie_id, item_id))
                        else:
                            # 处理字典类型的详情数据（向后兼容）
                            cursor.execute('''
                            UPDATE item_info SET
                                item_title = ?, item_description = ?, item_category = ?,
                                item_price = ?, item_detail = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE cookie_id = ? AND item_id = ?
                            ''', (
                                item_data.get('title', ''),
                                item_data.get('description', ''),
                                item_data.get('category', ''),
                                item_data.get('price', ''),
                                json.dumps(item_data, ensure_ascii=False),
                                cookie_id, item_id
                            ))
                        logger.info(f"更新商品信息（覆盖）: {item_id}")
                    else:
                        # 如果商品详情没有数据，则不更新，只记录存在
                        logger.debug(f"商品信息已存在，无新数据，跳过更新: {item_id}")
                        return True
                else:
                    # 新增商品信息
                    if isinstance(item_data, str):
                        # 直接保存字符串详情
                        cursor.execute('''
                        INSERT INTO item_info (cookie_id, item_id, item_detail)
                        VALUES (?, ?, ?)
                        ''', (cookie_id, item_id, item_data))
                    else:
                        # 处理字典类型的详情数据（向后兼容）
                        cursor.execute('''
                        INSERT INTO item_info (cookie_id, item_id, item_title, item_description,
                                             item_category, item_price, item_detail)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            cookie_id, item_id,
                            item_data.get('title', '') if item_data else '',
                            item_data.get('description', '') if item_data else '',
                            item_data.get('category', '') if item_data else '',
                            item_data.get('price', '') if item_data else '',
                            json.dumps(item_data, ensure_ascii=False) if item_data else ''
                        ))
                    logger.info(f"新增商品信息: {item_id}")

                self.conn.commit()
                return True

        except Exception as e:
            logger.error(f"保存商品信息失败: {e}")
            return False

    def get_item_info(self, cookie_id: str, item_id: str) -> Optional[Dict]:
        """获取商品信息

        Args:
            cookie_id: Cookie ID
            item_id: 商品ID

        Returns:
            Dict: 商品信息，如果不存在返回None
        """
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT * FROM item_info
                WHERE cookie_id = ? AND item_id = ?
                ''', (cookie_id, item_id))

                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    item_info = dict(zip(columns, row))

                    # 解析item_detail JSON
                    if item_info.get('item_detail'):
                        try:
                            item_info['item_detail_parsed'] = json.loads(item_info['item_detail'])
                        except:
                            item_info['item_detail_parsed'] = {}

                    return item_info
                return None

        except Exception as e:
            logger.error(f"获取商品信息失败: {e}")
            return None

    def get_items_by_cookie(self, cookie_id: str) -> List[Dict]:
        """获取指定Cookie的所有商品信息

        Args:
            cookie_id: Cookie ID

        Returns:
            List[Dict]: 商品信息列表
        """
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT * FROM item_info
                WHERE cookie_id = ?
                ORDER BY updated_at DESC
                ''', (cookie_id,))

                columns = [description[0] for description in cursor.description]
                items = []

                for row in cursor.fetchall():
                    item_info = dict(zip(columns, row))

                    # 解析item_detail JSON
                    if item_info.get('item_detail'):
                        try:
                            item_info['item_detail_parsed'] = json.loads(item_info['item_detail'])
                        except:
                            item_info['item_detail_parsed'] = {}

                    items.append(item_info)

                return items

        except Exception as e:
            logger.error(f"获取Cookie商品信息失败: {e}")
            return []

    def get_all_items(self) -> List[Dict]:
        """获取所有商品信息

        Returns:
            List[Dict]: 所有商品信息列表
        """
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT * FROM item_info
                ORDER BY updated_at DESC
                ''')

                columns = [description[0] for description in cursor.description]
                items = []

                for row in cursor.fetchall():
                    item_info = dict(zip(columns, row))

                    # 解析item_detail JSON
                    if item_info.get('item_detail'):
                        try:
                            item_info['item_detail_parsed'] = json.loads(item_info['item_detail'])
                        except:
                            item_info['item_detail_parsed'] = {}

                    items.append(item_info)

                return items

        except Exception as e:
            logger.error(f"获取所有商品信息失败: {e}")
            return []

    def update_item_detail(self, cookie_id: str, item_id: str, item_detail: str) -> bool:
        """更新商品详情（不覆盖商品标题等基本信息）

        Args:
            cookie_id: Cookie ID
            item_id: 商品ID
            item_detail: 商品详情JSON字符串

        Returns:
            bool: 操作是否成功
        """
        try:
            with self.lock:
                cursor = self.conn.cursor()
                # 只更新item_detail字段，不影响其他字段
                cursor.execute('''
                UPDATE item_info SET
                    item_detail = ?, updated_at = CURRENT_TIMESTAMP
                WHERE cookie_id = ? AND item_id = ?
                ''', (item_detail, cookie_id, item_id))

                if cursor.rowcount > 0:
                    self.conn.commit()
                    logger.info(f"更新商品详情成功: {item_id}")
                    return True
                else:
                    logger.warning(f"未找到要更新的商品: {item_id}")
                    return False

        except Exception as e:
            logger.error(f"更新商品详情失败: {e}")
            self.conn.rollback()
            return False

    def update_item_title_only(self, cookie_id: str, item_id: str, item_title: str) -> bool:
        """仅更新商品标题（并发安全）

        Args:
            cookie_id: Cookie ID
            item_id: 商品ID
            item_title: 商品标题

        Returns:
            bool: 操作是否成功
        """
        try:
            with self.lock:
                cursor = self.conn.cursor()
                # 使用 INSERT OR REPLACE 确保记录存在，但只更新标题字段
                cursor.execute('''
                INSERT INTO item_info (cookie_id, item_id, item_title, item_description,
                                     item_category, item_price, item_detail, created_at, updated_at)
                VALUES (?, ?, ?,
                       COALESCE((SELECT item_description FROM item_info WHERE cookie_id = ? AND item_id = ?), ''),
                       COALESCE((SELECT item_category FROM item_info WHERE cookie_id = ? AND item_id = ?), ''),
                       COALESCE((SELECT item_price FROM item_info WHERE cookie_id = ? AND item_id = ?), ''),
                       COALESCE((SELECT item_detail FROM item_info WHERE cookie_id = ? AND item_id = ?), ''),
                       COALESCE((SELECT created_at FROM item_info WHERE cookie_id = ? AND item_id = ?), CURRENT_TIMESTAMP),
                       CURRENT_TIMESTAMP)
                ON CONFLICT(cookie_id, item_id) DO UPDATE SET
                    item_title = excluded.item_title,
                    updated_at = CURRENT_TIMESTAMP
                ''', (cookie_id, item_id, item_title,
                      cookie_id, item_id, cookie_id, item_id, cookie_id, item_id,
                      cookie_id, item_id, cookie_id, item_id))

                self.conn.commit()
                logger.info(f"更新商品标题成功: {item_id} - {item_title}")
                return True

        except Exception as e:
            logger.error(f"更新商品标题失败: {e}")
            self.conn.rollback()
            return False

    def batch_save_item_basic_info(self, items_data: list) -> int:
        """批量保存商品基本信息（并发安全）

        Args:
            items_data: 商品数据列表，每个元素包含 cookie_id, item_id, item_title 等字段

        Returns:
            int: 成功保存的商品数量
        """
        if not items_data:
            return 0

        success_count = 0
        try:
            with self.lock:
                cursor = self.conn.cursor()

                # 使用事务批量处理
                cursor.execute('BEGIN TRANSACTION')

                for item_data in items_data:
                    try:
                        cookie_id = item_data.get('cookie_id')
                        item_id = item_data.get('item_id')
                        item_title = item_data.get('item_title', '')
                        item_description = item_data.get('item_description', '')
                        item_category = item_data.get('item_category', '')
                        item_price = item_data.get('item_price', '')
                        item_detail = item_data.get('item_detail', '')

                        if not cookie_id or not item_id:
                            continue

                        # 使用 INSERT OR IGNORE + UPDATE 模式
                        cursor.execute('''
                        INSERT OR IGNORE INTO item_info (cookie_id, item_id, item_title, item_description,
                                                       item_category, item_price, item_detail, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', (cookie_id, item_id, item_title, item_description,
                              item_category, item_price, item_detail))

                        if cursor.rowcount == 0:
                            # 记录已存在，进行条件更新
                            update_sql = '''
                            UPDATE item_info SET
                                item_title = CASE WHEN (item_title IS NULL OR item_title = '') AND ? != '' THEN ? ELSE item_title END,
                                item_description = CASE WHEN (item_description IS NULL OR item_description = '') AND ? != '' THEN ? ELSE item_description END,
                                item_category = CASE WHEN (item_category IS NULL OR item_category = '') AND ? != '' THEN ? ELSE item_category END,
                                item_price = CASE WHEN (item_price IS NULL OR item_price = '') AND ? != '' THEN ? ELSE item_price END,
                                item_detail = CASE WHEN (item_detail IS NULL OR item_detail = '' OR TRIM(item_detail) = '') AND ? != '' THEN ? ELSE item_detail END,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE cookie_id = ? AND item_id = ?
                            '''
                            cursor.execute(update_sql, (
                                item_title, item_title,
                                item_description, item_description,
                                item_category, item_category,
                                item_price, item_price,
                                item_detail, item_detail,
                                cookie_id, item_id
                            ))

                        success_count += 1

                    except Exception as item_e:
                        logger.warning(f"批量保存单个商品失败 {item_data.get('item_id', 'unknown')}: {item_e}")
                        continue

                cursor.execute('COMMIT')
                logger.info(f"批量保存商品信息完成: {success_count}/{len(items_data)} 个商品")
                return success_count

        except Exception as e:
            logger.error(f"批量保存商品信息失败: {e}")
            try:
                cursor.execute('ROLLBACK')
            except:
                pass
            return success_count

    def delete_item_info(self, cookie_id: str, item_id: str) -> bool:
        """删除商品信息

        Args:
            cookie_id: Cookie ID
            item_id: 商品ID

        Returns:
            bool: 操作是否成功
        """
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM item_info WHERE cookie_id = ? AND item_id = ?',
                             (cookie_id, item_id))

                if cursor.rowcount > 0:
                    self.conn.commit()
                    logger.info(f"删除商品信息成功: {cookie_id} - {item_id}")
                    return True
                else:
                    logger.warning(f"未找到要删除的商品信息: {cookie_id} - {item_id}")
                    return False

        except Exception as e:
            logger.error(f"删除商品信息失败: {e}")
            self.conn.rollback()
            return False

    def batch_delete_item_info(self, items_to_delete: list) -> int:
        """批量删除商品信息

        Args:
            items_to_delete: 要删除的商品列表，每个元素包含 cookie_id 和 item_id

        Returns:
            int: 成功删除的商品数量
        """
        if not items_to_delete:
            return 0

        success_count = 0
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('BEGIN TRANSACTION')

                for item_data in items_to_delete:
                    try:
                        cookie_id = item_data.get('cookie_id')
                        item_id = item_data.get('item_id')

                        if not cookie_id or not item_id:
                            continue

                        cursor.execute('DELETE FROM item_info WHERE cookie_id = ? AND item_id = ?',
                                     (cookie_id, item_id))

                        if cursor.rowcount > 0:
                            success_count += 1
                            logger.debug(f"删除商品信息: {cookie_id} - {item_id}")

                    except Exception as item_e:
                        logger.warning(f"删除单个商品失败 {item_data.get('item_id', 'unknown')}: {item_e}")
                        continue

                cursor.execute('COMMIT')
                logger.info(f"批量删除商品信息完成: {success_count}/{len(items_to_delete)} 个商品")
                return success_count

        except Exception as e:
            logger.error(f"批量删除商品信息失败: {e}")
            try:
                cursor.execute('ROLLBACK')
            except:
                pass
            return success_count


# 全局单例
db_manager = DBManager()

# 确保进程结束时关闭数据库连接
import atexit
atexit.register(db_manager.close)