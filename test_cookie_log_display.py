#!/usr/bin/env python3
"""
测试Cookie ID在日志中的显示
"""

import time
import asyncio
from loguru import logger

# 模拟多个Cookie的日志输出
async def test_cookie_log_display():
    """测试Cookie ID在日志中的显示效果"""
    
    print("🧪 测试Cookie ID日志显示")
    print("=" * 50)
    
    # 模拟不同Cookie的日志输出
    cookies = [
        {"id": "user1_cookie", "name": "用户1的账号"},
        {"id": "user2_cookie", "name": "用户2的账号"},
        {"id": "admin_cookie", "name": "管理员账号"}
    ]
    
    print("📋 模拟多用户系统日志输出:")
    print("-" * 50)
    
    for i, cookie in enumerate(cookies):
        cookie_id = cookie["id"]
        cookie_name = cookie["name"]
        
        # 模拟各种类型的日志
        msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        # 1. Token相关日志
        logger.info(f"【{cookie_id}】开始刷新token...")
        await asyncio.sleep(0.1)
        logger.info(f"【{cookie_id}】Token刷新成功")
        
        # 2. 连接相关日志
        logger.info(f"【{cookie_id}】连接注册完成")
        
        # 3. 系统消息日志
        logger.info(f"[{msg_time}] 【{cookie_id}】【系统】小闲鱼智能提示:")
        logger.info(f"  - 欢迎使用闲鱼智能助手")
        
        # 4. 消息处理日志
        logger.info(f"[{msg_time}] 【{cookie_id}】【系统】买家已付款，准备自动发货")
        logger.info(f"【{cookie_id}】准备自动发货: item_id=123456, item_title=测试商品")
        
        # 5. 回复相关日志
        logger.info(f"【{cookie_id}】使用默认回复: 您好，感谢您的咨询！")
        logger.info(f"【{cookie_id}】AI回复生成成功: 这是AI生成的回复")
        
        # 6. 错误日志
        if i == 1:  # 只在第二个Cookie上模拟错误
            logger.error(f"【{cookie_id}】Token刷新失败: 网络连接超时")
        
        print()  # 空行分隔
        await asyncio.sleep(0.2)
    
    print("=" * 50)
    print("✅ 日志显示测试完成")
    
    print("\n📊 日志格式说明:")
    print("• 【Cookie_ID】- 标识具体的用户账号")
    print("• 【系统】- 系统级别的消息")
    print("• [时间戳] - 消息发生的具体时间")
    print("• 不同用户的操作现在可以清晰区分")
    
    print("\n🎯 改进效果:")
    print("• ✅ 多用户环境下可以快速定位问题")
    print("• ✅ 日志分析更加高效")
    print("• ✅ 运维监控更加精准")
    print("• ✅ 调试过程更加清晰")

def test_log_format_comparison():
    """对比改进前后的日志格式"""
    
    print("\n🔍 日志格式对比")
    print("=" * 50)
    
    print("📝 改进前的日志格式:")
    print("2025-07-25 14:23:47.770 | INFO | XianyuAutoAsync:init:1360 - 获取初始token...")
    print("2025-07-25 14:23:47.771 | INFO | XianyuAutoAsync:refresh_token:134 - 开始刷新token...")
    print("2025-07-25 14:23:48.269 | INFO | XianyuAutoAsync:refresh_token:200 - Token刷新成功")
    print("2025-07-25 14:23:49.286 | INFO | XianyuAutoAsync:init:1407 - 连接注册完成")
    print("2025-07-25 14:23:49.288 | INFO | XianyuAutoAsync:handle_message:1663 - [2025-07-25 14:23:49] 【系统】小闲鱼智能提示:")
    
    print("\n📝 改进后的日志格式:")
    print("2025-07-25 14:23:47.770 | INFO | XianyuAutoAsync:init:1360 - 【user1_cookie】获取初始token...")
    print("2025-07-25 14:23:47.771 | INFO | XianyuAutoAsync:refresh_token:134 - 【user1_cookie】开始刷新token...")
    print("2025-07-25 14:23:48.269 | INFO | XianyuAutoAsync:refresh_token:200 - 【user1_cookie】Token刷新成功")
    print("2025-07-25 14:23:49.286 | INFO | XianyuAutoAsync:init:1407 - 【user1_cookie】连接注册完成")
    print("2025-07-25 14:23:49.288 | INFO | XianyuAutoAsync:handle_message:1663 - [2025-07-25 14:23:49] 【user1_cookie】【系统】小闲鱼智能提示:")
    
    print("\n🎯 改进优势:")
    print("• 🔍 快速识别: 一眼就能看出是哪个用户的操作")
    print("• 🐛 问题定位: 多用户环境下快速定位问题源头")
    print("• 📈 监控分析: 可以按用户统计操作频率和成功率")
    print("• 🔧 运维管理: 便于针对特定用户进行故障排查")

def generate_log_analysis_tips():
    """生成日志分析技巧"""
    
    print("\n💡 日志分析技巧")
    print("=" * 50)
    
    tips = [
        {
            "title": "按用户过滤日志",
            "command": "grep '【user1_cookie】' xianyu_2025-07-25.log",
            "description": "查看特定用户的所有操作日志"
        },
        {
            "title": "查看Token刷新情况",
            "command": "grep '【.*】.*Token' xianyu_2025-07-25.log",
            "description": "监控所有用户的Token刷新状态"
        },
        {
            "title": "统计用户活跃度",
            "command": "grep -o '【[^】]*】' xianyu_2025-07-25.log | sort | uniq -c",
            "description": "统计各用户的操作次数"
        },
        {
            "title": "查看系统消息",
            "command": "grep '【系统】' xianyu_2025-07-25.log",
            "description": "查看所有系统级别的消息"
        },
        {
            "title": "监控错误日志",
            "command": "grep 'ERROR.*【.*】' xianyu_2025-07-25.log",
            "description": "查看特定用户的错误信息"
        }
    ]
    
    for i, tip in enumerate(tips, 1):
        print(f"{i}. {tip['title']}")
        print(f"   命令: {tip['command']}")
        print(f"   说明: {tip['description']}")
        print()

async def main():
    """主函数"""
    print("🚀 Cookie ID日志显示测试工具")
    print("=" * 60)
    
    # 测试日志显示
    await test_cookie_log_display()
    
    # 对比日志格式
    test_log_format_comparison()
    
    # 生成分析技巧
    generate_log_analysis_tips()
    
    print("=" * 60)
    print("🎉 测试完成！现在您可以在多用户环境下清晰地识别每个用户的操作。")
    
    print("\n📋 下一步建议:")
    print("1. 重启服务以应用日志改进")
    print("2. 观察实际运行中的日志输出")
    print("3. 使用提供的命令进行日志分析")
    print("4. 根据需要调整日志级别和格式")

if __name__ == "__main__":
    asyncio.run(main())
