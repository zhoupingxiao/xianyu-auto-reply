"""
闲鱼订单详情获取工具
基于Playwright实现订单详情页面访问和数据提取
"""

import asyncio
import time
import sys
import os
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

# 修复Docker环境中的asyncio事件循环策略问题
if sys.platform.startswith('linux') or os.getenv('DOCKER_ENV'):
    try:
        # 在Linux/Docker环境中设置事件循环策略
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    except Exception as e:
        logger.warning(f"设置事件循环策略失败: {e}")

# 确保在Docker环境中使用正确的事件循环
if os.getenv('DOCKER_ENV'):
    try:
        # 强制使用SelectorEventLoop（在Docker中更稳定）
        if hasattr(asyncio, 'SelectorEventLoop'):
            loop = asyncio.SelectorEventLoop()
            asyncio.set_event_loop(loop)
    except Exception as e:
        logger.warning(f"设置SelectorEventLoop失败: {e}")


class OrderDetailFetcher:
    """闲鱼订单详情获取器"""

    def __init__(self, cookie_string: str = None):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 请求头配置
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,ru;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }

        # Cookie配置 - 支持动态传入
        self.cookie = cookie_string

    async def init_browser(self, headless: bool = True):
        """初始化浏览器"""
        try:
            playwright = await async_playwright().start()
            
            # 启动浏览器（Docker环境优化）
            browser_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-extensions',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--hide-scrollbars',
                '--mute-audio',
                '--no-default-browser-check',
                '--no-pings',
                '--single-process'  # 在Docker中使用单进程模式
            ]

            # 在Docker环境中添加额外参数
            if os.getenv('DOCKER_ENV'):
                browser_args.extend([
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-client-side-phishing-detection',
                    '--disable-default-apps',
                    '--disable-hang-monitor',
                    '--disable-popup-blocking',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--disable-web-resources',
                    '--metrics-recording-only',
                    '--no-first-run',
                    '--safebrowsing-disable-auto-update',
                    '--enable-automation',
                    '--password-store=basic',
                    '--use-mock-keychain'
                ])

            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=browser_args
            )
            
            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            )
            
            # 设置额外的HTTP头
            await self.context.set_extra_http_headers(self.headers)
            
            # 创建页面
            self.page = await self.context.new_page()
            
            # 设置Cookie
            await self._set_cookies()
            
            logger.info("浏览器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            return False

    async def _set_cookies(self):
        """设置Cookie"""
        try:
            # 解析Cookie字符串
            cookies = []
            for cookie_pair in self.cookie.split('; '):
                if '=' in cookie_pair:
                    name, value = cookie_pair.split('=', 1)
                    cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.goofish.com',
                        'path': '/'
                    })
            
            # 添加Cookie到上下文
            await self.context.add_cookies(cookies)
            logger.info(f"已设置 {len(cookies)} 个Cookie")
            
        except Exception as e:
            logger.error(f"设置Cookie失败: {e}")

    async def fetch_order_detail(self, order_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        获取订单详情
        
        Args:
            order_id: 订单ID
            timeout: 超时时间（秒）
            
        Returns:
            包含订单详情的字典，失败时返回None
        """
        try:
            if not self.page:
                logger.error("浏览器未初始化")
                return None
            
            # 构建订单详情URL
            url = f"https://www.goofish.com/order-detail?orderId={order_id}&role=seller"
            logger.info(f"开始访问订单详情页面: {url}")
            
            # 访问页面
            response = await self.page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
            
            if not response or response.status != 200:
                logger.error(f"页面访问失败，状态码: {response.status if response else 'None'}")
                return None
            
            logger.info("页面加载成功，等待内容渲染...")
            
            # 等待页面完全加载
            await self.page.wait_for_load_state('networkidle')
            
            # 额外等待确保动态内容加载完成
            await asyncio.sleep(3)
            
            # 获取并解析SKU信息
            sku_info = await self._get_sku_content()

            # 获取页面标题
            title = await self.page.title()

            result = {
                'order_id': order_id,
                'url': url,
                'title': title,
                'sku_info': sku_info,  # 包含解析后的规格信息
                'spec_name': sku_info.get('spec_name', '') if sku_info else '',
                'spec_value': sku_info.get('spec_value', '') if sku_info else '',
                'timestamp': time.time()
            }

            logger.info(f"订单详情获取成功: {order_id}")
            if sku_info:
                logger.info(f"规格信息 - 名称: {result['spec_name']}, 值: {result['spec_value']}")
            return result
            
        except Exception as e:
            logger.error(f"获取订单详情失败: {e}")
            return None

    def _parse_sku_content(self, sku_content: str) -> Dict[str, str]:
        """
        解析SKU内容，根据冒号分割规格名称和规格值

        Args:
            sku_content: 原始SKU内容字符串

        Returns:
            包含规格名称和规格值的字典，如果解析失败则返回空字典
        """
        try:
            if not sku_content or ':' not in sku_content:
                logger.warning(f"SKU内容格式无效或不包含冒号: {sku_content}")
                return {}

            # 根据冒号分割
            parts = sku_content.split(':', 1)  # 只分割第一个冒号

            if len(parts) == 2:
                spec_name = parts[0].strip()
                spec_value = parts[1].strip()

                if spec_name and spec_value:
                    result = {
                        'spec_name': spec_name,
                        'spec_value': spec_value
                    }
                    logger.info(f"SKU解析成功 - 规格名称: {spec_name}, 规格值: {spec_value}")
                    return result
                else:
                    logger.warning(f"SKU解析失败，规格名称或值为空: 名称='{spec_name}', 值='{spec_value}'")
                    return {}
            else:
                logger.warning(f"SKU内容分割失败: {sku_content}")
                return {}

        except Exception as e:
            logger.error(f"解析SKU内容异常: {e}")
            return {}

    async def _get_sku_content(self) -> Optional[Dict[str, str]]:
        """获取并解析SKU内容"""
        try:
            # 等待SKU元素出现
            sku_selector = '.sku--u_ddZval'

            # 检查元素是否存在
            sku_element = await self.page.query_selector(sku_selector)

            if sku_element:
                # 获取元素文本内容
                sku_content = await sku_element.text_content()
                if sku_content:
                    sku_content = sku_content.strip()
                    logger.info(f"找到SKU原始内容: {sku_content}")
                    print(f"🛍️ SKU原始内容: {sku_content}")

                    # 解析SKU内容
                    parsed_sku = self._parse_sku_content(sku_content)
                    if parsed_sku:
                        print(f"📋 规格名称: {parsed_sku['spec_name']}")
                        print(f"📝 规格值: {parsed_sku['spec_value']}")
                        return parsed_sku
                    else:
                        logger.warning("SKU内容解析失败")
                        return {}
                else:
                    logger.warning("SKU元素内容为空")
                    return {}
            else:
                logger.warning("未找到SKU元素")

                # 尝试获取页面的所有class包含sku的元素
                all_sku_elements = await self.page.query_selector_all('[class*="sku"]')
                if all_sku_elements:
                    logger.info(f"找到 {len(all_sku_elements)} 个包含'sku'的元素")
                    for i, element in enumerate(all_sku_elements):
                        class_name = await element.get_attribute('class')
                        text_content = await element.text_content()
                        logger.info(f"SKU元素 {i+1}: class='{class_name}', text='{text_content}'")

                return {}

        except Exception as e:
            logger.error(f"获取SKU内容失败: {e}")
            return {}

    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 便捷函数
async def fetch_order_detail_simple(order_id: str, cookie_string: str = None, headless: bool = True) -> Optional[Dict[str, Any]]:
    """
    简单的订单详情获取函数

    Args:
        order_id: 订单ID
        cookie_string: Cookie字符串，如果不提供则使用默认值
        headless: 是否无头模式

    Returns:
        订单详情字典或None
    """
    fetcher = OrderDetailFetcher(cookie_string)
    try:
        if await fetcher.init_browser(headless=headless):
            return await fetcher.fetch_order_detail(order_id)
    finally:
        await fetcher.close()
    return None


# 测试代码
if __name__ == "__main__":
    async def test():
        # 测试订单ID
        test_order_id = "2856024697612814489"
        
        print(f"🔍 开始获取订单详情: {test_order_id}")
        
        result = await fetch_order_detail_simple(test_order_id, headless=False)
        
        if result:
            print("✅ 订单详情获取成功:")
            print(f"📋 订单ID: {result['order_id']}")
            print(f"🌐 URL: {result['url']}")
            print(f"📄 页面标题: {result['title']}")
            print(f"🛍️ SKU内容: {result['sku_content']}")
        else:
            print("❌ 订单详情获取失败")
    
    # 运行测试
    asyncio.run(test())
