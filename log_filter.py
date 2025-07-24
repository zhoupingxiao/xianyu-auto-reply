#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志过滤器
用于过滤不需要记录到文件的日志
"""

import re
from typing import Dict, Any

class LogFilter:
    """日志过滤器类"""
    
    def __init__(self):
        # 不需要记录的API路径模式
        self.excluded_api_patterns = [
            r'GET /logs',
            r'GET /logs/stats',
            r'GET /health',
            r'GET /docs',
            r'GET /redoc',
            r'GET /openapi\.json',
            r'GET /static/',
            r'GET /favicon\.ico'
        ]
        
        # 不需要记录的消息模式
        self.excluded_message_patterns = [
            r'API请求: GET /logs',
            r'API响应: GET /logs',
            r'API请求: GET /health',
            r'API响应: GET /health',
            r'API请求: GET /docs',
            r'API响应: GET /docs',
            r'API请求: GET /static/',
            r'API响应: GET /static/',
            r'.*favicon\.ico.*',
            r'.*websocket.*ping.*',
            r'.*websocket.*pong.*'
        ]
        
        # 编译正则表达式以提高性能
        self.compiled_api_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.excluded_api_patterns]
        self.compiled_message_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.excluded_message_patterns]
    
    def should_log(self, record: Dict[str, Any]) -> bool:
        """
        判断是否应该记录这条日志
        
        Args:
            record: loguru的日志记录字典
            
        Returns:
            bool: True表示应该记录，False表示应该过滤掉
        """
        try:
            message = record.get('message', '')
            
            # 检查消息模式
            for pattern in self.compiled_message_patterns:
                if pattern.search(message):
                    return False
            
            # 检查API路径模式
            for pattern in self.compiled_api_patterns:
                if pattern.search(message):
                    return False
            
            # 过滤掉过于频繁的心跳日志
            if any(keyword in message.lower() for keyword in ['heartbeat', '心跳', 'ping', 'pong']):
                return False
            
            # 过滤掉WebSocket连接状态的频繁日志
            if any(keyword in message.lower() for keyword in ['websocket connected', 'websocket disconnected']):
                # 只记录连接和断开，不记录频繁的状态检查
                if 'status check' in message.lower():
                    return False
            
            return True
            
        except Exception:
            # 如果过滤器出错，默认记录日志
            return True

# 全局日志过滤器实例
log_filter = LogFilter()

def filter_log_record(record):
    """
    loguru的过滤器函数
    
    Args:
        record: loguru的日志记录对象
        
    Returns:
        bool: True表示应该记录，False表示应该过滤掉
    """
    return log_filter.should_log(record)

def add_excluded_pattern(pattern: str):
    """
    添加新的排除模式
    
    Args:
        pattern: 正则表达式模式
    """
    log_filter.excluded_message_patterns.append(pattern)
    log_filter.compiled_message_patterns.append(re.compile(pattern, re.IGNORECASE))

def remove_excluded_pattern(pattern: str):
    """
    移除排除模式
    
    Args:
        pattern: 要移除的正则表达式模式
    """
    if pattern in log_filter.excluded_message_patterns:
        index = log_filter.excluded_message_patterns.index(pattern)
        log_filter.excluded_message_patterns.pop(index)
        log_filter.compiled_message_patterns.pop(index)

def get_excluded_patterns():
    """
    获取当前的排除模式列表
    
    Returns:
        list: 排除模式列表
    """
    return log_filter.excluded_message_patterns.copy()

# 测试函数
def test_filter():
    """测试过滤器功能"""
    test_messages = [
        "🌐 API请求: GET /logs?lines=200",
        "✅ API响应: GET /logs - 200 (0.123s)",
        "🌐 API请求: GET /health",
        "✅ API响应: GET /health - 200 (0.001s)",
        "🌐 API请求: POST /cookies",
        "✅ API响应: POST /cookies - 201 (0.456s)",
        "WebSocket心跳检查",
        "用户登录成功",
        "数据库连接建立",
        "WebSocket connected status check",
        "处理消息: 你好"
    ]
    
    print("🧪 测试日志过滤器")
    print("=" * 50)
    
    for message in test_messages:
        record = {"message": message}
        should_log = log_filter.should_log(record)
        status = "✅ 记录" if should_log else "❌ 过滤"
        print(f"{status}: {message}")
    
    print("=" * 50)
    print("测试完成")

if __name__ == "__main__":
    test_filter()
