#!/usr/bin/env python3
"""
测试修复
"""

def test_imports():
    print("🧪 测试导入修复")
    
    try:
        from file_log_collector import setup_file_logging, get_file_log_collector
        print("✅ file_log_collector 导入成功")
        
        # 测试初始化
        collector = setup_file_logging()
        print("✅ 文件日志收集器初始化成功")
        
        # 生成测试日志
        from loguru import logger
        logger.info("测试日志修复")
        
        print("✅ 所有导入和初始化都正常")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")

if __name__ == "__main__":
    test_imports()
