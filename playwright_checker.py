#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright 可用性检查工具
在系统启动时检查 Playwright 是否正常工作
"""

import asyncio
import sys
import os
from loguru import logger

async def check_playwright_availability():
    """检查 Playwright 是否可用"""
    try:
        from playwright.async_api import async_playwright
        
        logger.info("正在检查 Playwright 可用性...")
        
        async with async_playwright() as p:
            # 尝试启动浏览器
            browser = await p.chromium.launch(headless=True)
            
            # 创建页面
            page = await browser.new_page()
            
            # 访问一个简单的页面
            await page.goto("data:text/html,<html><body><h1>Test</h1></body></html>")
            
            # 获取页面标题
            title = await page.title()
            
            # 关闭浏览器
            await browser.close()
            
            logger.info("✅ Playwright 检查通过，功能正常")
            return True
            
    except ImportError as e:
        logger.error(f"❌ Playwright 模块未安装: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Playwright 检查失败: {e}")
        return False

def check_playwright_sync():
    """同步版本的 Playwright 检查"""
    try:
        # 在 Docker 环境中设置事件循环策略
        if sys.platform.startswith('linux') or os.getenv('DOCKER_ENV'):
            try:
                asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
            except Exception as e:
                logger.warning(f"设置事件循环策略失败: {e}")
        
        # 运行异步检查
        return asyncio.run(check_playwright_availability())
    except Exception as e:
        logger.error(f"❌ Playwright 同步检查失败: {e}")
        return False

if __name__ == "__main__":
    # 命令行测试
    success = check_playwright_sync()
    if success:
        print("Playwright 可用性检查: 通过")
        sys.exit(0)
    else:
        print("Playwright 可用性检查: 失败")
        sys.exit(1)
