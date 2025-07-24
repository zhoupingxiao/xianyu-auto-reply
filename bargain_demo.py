#!/usr/bin/env python3
"""
议价功能演示脚本
展示AI回复的议价轮数限制功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_reply_engine import ai_reply_engine
from db_manager import db_manager

def simulate_bargain_conversation():
    """模拟议价对话流程"""
    print("🎭 模拟议价对话流程")
    print("=" * 50)
    
    # 测试参数
    cookie_id = "demo_account_001"
    chat_id = "demo_chat_001"
    user_id = "customer_001"
    item_id = "item_12345"
    user_name = "小明"
    
    # 商品信息
    item_info = {
        'title': 'iPhone 14 Pro 256GB 深空黑色',
        'price': 8999,
        'desc': '全新未拆封，国行正品，支持全国联保'
    }
    
    # 设置AI回复配置（模拟）
    ai_settings = {
        'ai_enabled': True,
        'model_name': 'qwen-plus',
        'api_key': 'demo-key',
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'max_discount_percent': 10,  # 最大优惠10%
        'max_discount_amount': 500,  # 最大优惠500元
        'max_bargain_rounds': 3,     # 最大议价3轮
        'custom_prompts': ''
    }
    
    # 保存配置
    db_manager.save_ai_reply_settings(cookie_id, ai_settings)
    
    # 清理之前的对话
    try:
        with db_manager.lock:
            cursor = db_manager.conn.cursor()
            cursor.execute('DELETE FROM ai_conversations WHERE cookie_id = ? AND chat_id = ?', 
                         (cookie_id, chat_id))
            db_manager.conn.commit()
    except:
        pass
    
    print(f"📱 商品信息:")
    print(f"   标题: {item_info['title']}")
    print(f"   价格: ¥{item_info['price']}")
    print(f"   描述: {item_info['desc']}")
    
    print(f"\n⚙️ 议价设置:")
    print(f"   最大议价轮数: {ai_settings['max_bargain_rounds']}")
    print(f"   最大优惠百分比: {ai_settings['max_discount_percent']}%")
    print(f"   最大优惠金额: ¥{ai_settings['max_discount_amount']}")
    
    # 模拟议价对话
    bargain_messages = [
        "你好，这个iPhone能便宜点吗？",
        "8500能卖吗？",
        "8800行不行？最后一次了",
        "8700，真的不能再少了"
    ]
    
    print(f"\n💬 议价对话模拟:")
    print("-" * 30)
    
    for i, message in enumerate(bargain_messages, 1):
        print(f"\n第{i}轮议价:")
        print(f"👤 {user_name}: {message}")
        
        # 检查当前议价次数
        current_count = ai_reply_engine.get_bargain_count(chat_id, cookie_id)
        max_rounds = ai_settings['max_bargain_rounds']
        
        print(f"📊 当前议价次数: {current_count}/{max_rounds}")
        
        # 模拟意图检测为price
        intent = "price"
        
        # 检查是否超出限制
        if current_count >= max_rounds:
            print(f"🚫 已达到最大议价轮数限制！")
            refuse_reply = "抱歉，这个价格已经是最优惠的了，不能再便宜了哦！"
            print(f"🤖 AI回复: {refuse_reply}")
            
            # 保存对话记录
            ai_reply_engine.save_conversation(chat_id, cookie_id, user_id, item_id, "user", message, intent)
            ai_reply_engine.save_conversation(chat_id, cookie_id, user_id, item_id, "assistant", refuse_reply, intent)
            
            print(f"✋ 议价结束，系统拒绝继续议价")
            break
        else:
            # 模拟AI回复（因为没有真实API密钥，这里手动模拟）
            if i == 1:
                ai_reply = "您好！这个价格已经很优惠了，最多可以优惠200元，8799元怎么样？"
            elif i == 2:
                ai_reply = "8500太低了，我们再让一点，8699元，这已经是很大的优惠了！"
            elif i == 3:
                ai_reply = "好的，看您很有诚意，8799元成交，这真的是最低价了！"
            else:
                ai_reply = "抱歉，这个价格已经是最优惠的了！"
            
            print(f"🤖 AI回复: {ai_reply}")
            
            # 保存对话记录
            ai_reply_engine.save_conversation(chat_id, cookie_id, user_id, item_id, "user", message, intent)
            ai_reply_engine.save_conversation(chat_id, cookie_id, user_id, item_id, "assistant", ai_reply, intent)
    
    # 显示最终统计
    print(f"\n📈 最终统计:")
    final_count = ai_reply_engine.get_bargain_count(chat_id, cookie_id)
    print(f"   总议价轮数: {final_count}")
    print(f"   最大允许轮数: {max_rounds}")
    print(f"   是否达到限制: {'是' if final_count >= max_rounds else '否'}")

def show_bargain_features():
    """展示议价功能特性"""
    print(f"\n🎯 议价功能特性说明:")
    print("=" * 50)
    
    features = [
        "✅ 智能议价轮数统计：自动统计用户的议价次数",
        "✅ 灵活轮数限制：可配置最大议价轮数（1-10轮）",
        "✅ 优惠金额控制：设置最大优惠百分比和金额",
        "✅ 友好拒绝回复：超出限制时礼貌拒绝继续议价",
        "✅ 上下文感知：AI了解完整的议价历史",
        "✅ 个性化策略：根据议价轮数调整回复策略",
        "✅ 数据持久化：议价记录永久保存",
        "✅ 实时生效：配置修改后立即生效"
    ]
    
    for feature in features:
        print(f"   {feature}")
    
    print(f"\n💡 使用建议:")
    suggestions = [
        "设置合理的最大议价轮数（建议3-5轮）",
        "配合最大优惠百分比和金额使用",
        "在AI提示词中强调议价策略",
        "定期分析议价数据，优化策略",
        "根据商品类型调整议价参数"
    ]
    
    for suggestion in suggestions:
        print(f"   • {suggestion}")

def main():
    """主函数"""
    print("🚀 AI回复议价功能演示")
    
    # 模拟议价对话
    simulate_bargain_conversation()
    
    # 展示功能特性
    show_bargain_features()
    
    print(f"\n🎉 演示完成！")
    print(f"\n📋 下一步:")
    print(f"   1. 在Web界面配置真实的AI API密钥")
    print(f"   2. 为需要的账号启用AI回复功能")
    print(f"   3. 设置合适的议价参数")
    print(f"   4. 测试实际的议价效果")

if __name__ == "__main__":
    main()
