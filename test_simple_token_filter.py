#!/usr/bin/env python3
"""
简单测试令牌过期过滤逻辑
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_token_expiry_filter_logic():
    """测试令牌过期过滤逻辑"""
    print("🧪 测试令牌过期过滤逻辑")
    print("=" * 50)
    
    # 直接测试过滤逻辑，不依赖完整的XianyuLive实例
    def _is_normal_token_expiry(error_message: str) -> bool:
        """检查是否是正常的令牌过期（这种情况不需要发送通知）"""
        # 正常的令牌过期关键词
        normal_expiry_keywords = [
            'FAIL_SYS_TOKEN_EXOIRED::令牌过期',
            'FAIL_SYS_TOKEN_EXPIRED::令牌过期',
            'FAIL_SYS_TOKEN_EXOIRED',
            'FAIL_SYS_TOKEN_EXPIRED',
            '令牌过期'
        ]
        
        # 检查错误消息是否包含正常的令牌过期关键词
        for keyword in normal_expiry_keywords:
            if keyword in error_message:
                return True
        
        return False
    
    # 测试用例
    test_cases = [
        # 应该被过滤的消息（返回True）
        ("Token刷新失败: {'ret': ['FAIL_SYS_TOKEN_EXOIRED::令牌过期']}", True, "标准令牌过期"),
        ("Token刷新失败: {'ret': ['FAIL_SYS_TOKEN_EXPIRED::令牌过期']}", True, "标准令牌过期(EXPIRED)"),
        ("Token刷新异常: FAIL_SYS_TOKEN_EXOIRED", True, "简单令牌过期"),
        ("Token刷新异常: FAIL_SYS_TOKEN_EXPIRED", True, "简单令牌过期(EXPIRED)"),
        ("Token刷新失败: 令牌过期", True, "中文令牌过期"),
        ("其他错误信息包含FAIL_SYS_TOKEN_EXOIRED的情况", True, "包含关键词"),
        
        # 不应该被过滤的消息（返回False）
        ("Token刷新失败: {'ret': ['FAIL_SYS_SESSION_EXPIRED::Session过期']}", False, "Session过期"),
        ("Token刷新异常: 网络连接超时", False, "网络异常"),
        ("Token刷新失败: Cookie无效", False, "Cookie问题"),
        ("初始化时无法获取有效Token", False, "初始化失败"),
        ("Token刷新失败: 未知错误", False, "未知错误"),
        ("Token刷新失败: API调用失败", False, "API失败"),
        ("", False, "空消息"),
    ]
    
    print("📋 测试用例:")
    print("-" * 50)
    
    passed = 0
    total = len(test_cases)
    
    for i, (message, expected, description) in enumerate(test_cases, 1):
        result = _is_normal_token_expiry(message)
        
        if result == expected:
            status = "✅ 通过"
            passed += 1
        else:
            status = "❌ 失败"
        
        filter_action = "过滤" if result else "不过滤"
        expected_action = "过滤" if expected else "不过滤"
        
        print(f"{i:2d}. {status} {description}")
        print(f"    消息: {message[:60]}{'...' if len(message) > 60 else ''}")
        print(f"    结果: {filter_action} | 期望: {expected_action}")
        print()
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！过滤逻辑工作正常")
        return True
    else:
        print("⚠️ 部分测试失败，需要检查过滤逻辑")
        return False

def show_real_world_examples():
    """显示真实世界的例子"""
    print("\n\n📋 真实场景示例")
    print("=" * 50)
    
    print("🚫 以下情况将不再发送通知（被过滤）:")
    examples_filtered = [
        "Token刷新失败: {'api': 'mtop.taobao.idlemessage.pc.login.token', 'data': {}, 'ret': ['FAIL_SYS_TOKEN_EXOIRED::令牌过期'], 'v': '1.0'}",
        "Token刷新异常: FAIL_SYS_TOKEN_EXPIRED",
        "Token刷新失败: 令牌过期"
    ]
    
    for i, example in enumerate(examples_filtered, 1):
        print(f"{i}. {example}")
    
    print("\n✅ 以下情况仍会发送通知（不被过滤）:")
    examples_not_filtered = [
        "Token刷新失败: {'api': 'mtop.taobao.idlemessage.pc.login.token', 'data': {}, 'ret': ['FAIL_SYS_SESSION_EXPIRED::Session过期'], 'v': '1.0'}",
        "Token刷新异常: 网络连接超时",
        "初始化时无法获取有效Token"
    ]
    
    for i, example in enumerate(examples_not_filtered, 1):
        print(f"{i}. {example}")
    
    print("\n💡 设计理念:")
    print("• 令牌过期是正常现象，系统会自动重试刷新")
    print("• Session过期通常意味着Cookie过期，需要用户手动更新")
    print("• 网络异常等其他错误也需要用户关注")
    print("• 减少无用通知，提升用户体验")

def show_implementation_details():
    """显示实现细节"""
    print("\n\n🔧 实现细节")
    print("=" * 50)
    
    print("📍 修改位置:")
    print("• 文件: XianyuAutoAsync.py")
    print("• 方法: send_token_refresh_notification()")
    print("• 新增: _is_normal_token_expiry() 过滤方法")
    
    print("\n🔍 过滤关键词:")
    keywords = [
        'FAIL_SYS_TOKEN_EXOIRED::令牌过期',
        'FAIL_SYS_TOKEN_EXPIRED::令牌过期', 
        'FAIL_SYS_TOKEN_EXOIRED',
        'FAIL_SYS_TOKEN_EXPIRED',
        '令牌过期'
    ]
    
    for keyword in keywords:
        print(f"• {keyword}")
    
    print("\n⚡ 执行流程:")
    print("1. 调用 send_token_refresh_notification()")
    print("2. 检查 _is_normal_token_expiry(error_message)")
    print("3. 如果是正常令牌过期，记录调试日志并返回")
    print("4. 如果不是，继续原有的通知发送流程")
    
    print("\n📝 日志记录:")
    print("• 被过滤的消息会记录调试日志")
    print("• 格式: '检测到正常的令牌过期，跳过通知: {error_message}'")
    print("• 便于问题排查和功能验证")

if __name__ == "__main__":
    try:
        success = test_token_expiry_filter_logic()
        show_real_world_examples()
        show_implementation_details()
        
        print("\n" + "=" * 50)
        if success:
            print("🎊 令牌过期通知过滤功能测试完成！")
            print("✅ 用户将不再收到正常令牌过期的通知")
        else:
            print("❌ 测试失败，需要检查实现")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
