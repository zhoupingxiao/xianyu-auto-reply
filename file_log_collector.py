#!/usr/bin/env python3
"""
基于文件监控的日志收集器
"""

import os
import re
import time
import threading
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class FileLogCollector:
    """基于文件监控的日志收集器"""
    
    def __init__(self, max_logs: int = 2000):
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        self.lock = threading.Lock()
        
        # 日志文件路径
        self.log_file = None
        self.last_position = 0
        
        # 启动文件监控
        self.setup_file_monitoring()
    
    def setup_file_monitoring(self):
        """设置文件监控"""
        # 使用统一的日志文件路径
        import time
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)

        # 使用与其他模块相同的日志文件命名规则
        today_log = os.path.join(log_dir, f"xianyu_{time.strftime('%Y-%m-%d')}.log")

        # 查找日志文件，优先使用今天的日志文件
        possible_files = [
            today_log,
            "logs/xianyu.log",
            "xianyu.log",
            "app.log",
            "system.log",
            "logs/app.log"
        ]

        for file_path in possible_files:
            if os.path.exists(file_path):
                self.log_file = file_path
                break

        if not self.log_file:
            # 如果没有找到现有文件，使用今天的日志文件
            self.log_file = today_log

        print(f"日志收集器监控文件: {self.log_file}")

        # 启动文件监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_file, daemon=True)
        self.monitor_thread.start()
    

    
    def monitor_file(self):
        """监控日志文件变化"""
        print(f"开始监控日志文件: {self.log_file}")

        while True:
            try:
                if os.path.exists(self.log_file):
                    # 获取文件大小
                    file_size = os.path.getsize(self.log_file)

                    if file_size > self.last_position:
                        # 读取新增内容
                        try:
                            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                                f.seek(self.last_position)
                                new_lines = f.readlines()
                                self.last_position = f.tell()

                            # 解析新增的日志行
                            for line in new_lines:
                                line = line.strip()
                                if line:  # 只处理非空行
                                    self.parse_log_line(line)
                        except Exception as read_error:
                            print(f"读取日志文件失败: {read_error}")
                    elif file_size < self.last_position:
                        # 文件被截断或重新创建，重置位置
                        self.last_position = 0
                        print(f"检测到日志文件被重置: {self.log_file}")
                else:
                    # 文件不存在，重置位置等待文件创建
                    self.last_position = 0

                time.sleep(0.2)  # 每0.2秒检查一次，更及时

            except Exception as e:
                print(f"监控日志文件异常: {e}")
                time.sleep(1)  # 出错时等待1秒
    
    def parse_log_line(self, line: str):
        """解析日志行"""
        if not line:
            return

        try:
            # 解析统一格式的日志
            # 格式: 2024-07-24 15:46:03.430 | INFO | module_name:function_name:123 - 消息内容
            pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| (\w+) \| ([^:]+):([^:]+):(\d+) - (.*)'
            match = re.match(pattern, line)

            if match:
                timestamp_str, level, source, function, line_num, message = match.groups()

                # 转换时间格式
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                except:
                    timestamp = datetime.now()

                # 清理source名称，移除路径和扩展名
                if '\\' in source or '/' in source:
                    source = os.path.basename(source)
                if source.endswith('.py'):
                    source = source[:-3]

                log_entry = {
                    "timestamp": timestamp.isoformat(),
                    "level": level.strip(),
                    "source": source.strip(),
                    "function": function.strip(),
                    "line": int(line_num),
                    "message": message.strip()
                }

                with self.lock:
                    self.logs.append(log_entry)

            else:
                # 尝试解析其他可能的格式
                # 简单格式: [时间] [级别] 消息
                simple_pattern = r'\[([^\]]+)\] \[(\w+)\] (.*)'
                simple_match = re.match(simple_pattern, line)

                if simple_match:
                    timestamp_str, level, message = simple_match.groups()
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    except:
                        timestamp = datetime.now()

                    log_entry = {
                        "timestamp": timestamp.isoformat(),
                        "level": level.strip(),
                        "source": "system",
                        "function": "unknown",
                        "line": 0,
                        "message": message.strip()
                    }

                    with self.lock:
                        self.logs.append(log_entry)
                else:
                    # 如果都解析失败，作为普通消息处理
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "source": "system",
                        "function": "unknown",
                        "line": 0,
                        "message": line.strip()
                    }

                    with self.lock:
                        self.logs.append(log_entry)

        except Exception as e:
            # 如果解析失败，作为普通消息处理
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "source": "log_parser",
                "function": "parse_log_line",
                "line": 0,
                "message": f"日志解析失败: {line} (错误: {str(e)})"
            }

            with self.lock:
                self.logs.append(log_entry)
    
    def get_logs(self, lines: int = 200, level_filter: str = None, source_filter: str = None) -> List[Dict]:
        """获取日志记录"""
        with self.lock:
            logs_list = list(self.logs)
        
        # 应用过滤器
        if level_filter:
            logs_list = [log for log in logs_list if log['level'] == level_filter]
        
        if source_filter:
            logs_list = [log for log in logs_list if source_filter.lower() in log['source'].lower()]
        
        # 返回最后N行
        return logs_list[-lines:] if len(logs_list) > lines else logs_list
    
    def clear_logs(self):
        """清空日志"""
        with self.lock:
            self.logs.clear()
    
    def get_stats(self) -> Dict:
        """获取日志统计信息"""
        with self.lock:
            total_logs = len(self.logs)
            
            # 统计各级别日志数量
            level_counts = {}
            source_counts = {}
            
            for log in self.logs:
                level = log['level']
                source = log['source']
                
                level_counts[level] = level_counts.get(level, 0) + 1
                source_counts[source] = source_counts.get(source, 0) + 1
            
            return {
                "total_logs": total_logs,
                "level_counts": level_counts,
                "source_counts": source_counts,
                "max_capacity": self.max_logs,
                "log_file": self.log_file
            }


# 全局文件日志收集器实例
_file_collector = None
_file_collector_lock = threading.Lock()


def get_file_log_collector() -> FileLogCollector:
    """获取全局文件日志收集器实例"""
    global _file_collector
    
    if _file_collector is None:
        with _file_collector_lock:
            if _file_collector is None:
                _file_collector = FileLogCollector(max_logs=2000)
    
    return _file_collector


def setup_file_logging():
    """设置文件日志系统"""
    collector = get_file_log_collector()
    return collector


if __name__ == "__main__":
    # 测试文件日志收集器
    collector = setup_file_logging()
    
    # 生成一些测试日志
    from loguru import logger
    
    logger.info("文件日志收集器测试开始")
    logger.debug("这是调试信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.info("文件日志收集器测试结束")
    
    # 等待文件写入和监控
    time.sleep(2)
    
    # 获取日志
    logs = collector.get_logs(10)
    print(f"收集到 {len(logs)} 条日志:")
    for log in logs:
        print(f"  [{log['level']}] {log['source']}: {log['message']}")
    
    # 获取统计信息
    stats = collector.get_stats()
    print(f"\n统计信息: {stats}")
