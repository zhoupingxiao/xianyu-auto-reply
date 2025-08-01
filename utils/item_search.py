#!/usr/bin/env python3
"""
闲鱼商品搜索模块
基于 Playwright 实现真实的闲鱼商品搜索功能
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
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

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright 未安装，将使用模拟数据")


class XianyuSearcher:
    """闲鱼商品搜索器 - 基于 Playwright"""

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.api_responses = []

    async def safe_get(self, data, *keys, default="暂无"):
        """安全获取嵌套字典值"""
        for key in keys:
            try:
                data = data[key]
            except (KeyError, TypeError, IndexError):
                return default
        return data

    async def init_browser(self):
        """初始化浏览器"""
        if not PLAYWRIGHT_AVAILABLE:
            raise Exception("Playwright 未安装，无法使用真实搜索功能")

        if not self.browser:
            playwright = await async_playwright().start()
            logger.info("正在启动浏览器...")
            # Docker环境优化的浏览器启动参数
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
                headless=True,  # 无头模式
                args=browser_args
            )
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self.page = await self.context.new_page()

    async def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
    
    async def search_items(self, keyword: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        搜索闲鱼商品 - 使用 Playwright 获取真实数据

        Args:
            keyword: 搜索关键词
            page: 页码，从1开始
            page_size: 每页数量

        Returns:
            搜索结果字典，包含items列表和总数
        """
        try:
            if not PLAYWRIGHT_AVAILABLE:
                logger.error("Playwright 不可用，无法获取真实数据")
                return {
                    'items': [],
                    'total': 0,
                    'error': 'Playwright 不可用，无法获取真实数据'
                }

            logger.info(f"使用 Playwright 搜索闲鱼商品: 关键词='{keyword}', 页码={page}, 每页={page_size}")

            await self.init_browser()

            # 清空之前的API响应
            self.api_responses = []
            data_list = []

            # 设置API响应监听器
            async def on_response(response):
                """处理API响应，解析数据"""
                if "h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search" in response.url:
                    try:
                        # 检查响应状态
                        if response.status != 200:
                            logger.warning(f"API响应状态异常: {response.status}")
                            return

                        # 安全地获取响应内容
                        try:
                            result_json = await response.json()
                        except Exception as json_error:
                            logger.warning(f"无法解析响应JSON: {str(json_error)}")
                            return

                        self.api_responses.append(result_json)
                        logger.info(f"捕获到API响应，URL: {response.url}")

                        items = result_json.get("data", {}).get("resultList", [])
                        logger.info(f"从API获取到 {len(items)} 条原始数据")

                        for item in items:
                            try:
                                parsed_item = await self._parse_real_item(item)
                                if parsed_item:
                                    data_list.append(parsed_item)
                            except Exception as parse_error:
                                logger.warning(f"解析单个商品失败: {str(parse_error)}")
                                continue

                    except Exception as e:
                        logger.warning(f"响应处理异常: {str(e)}")

            try:
                logger.info("正在访问闲鱼首页...")
                await self.page.goto("https://www.goofish.com", timeout=30000)
                await self.page.wait_for_load_state("networkidle", timeout=10000)

                logger.info(f"正在搜索关键词: {keyword}")
                await self.page.fill('input[class*="search-input"]', keyword)

                # 注册响应监听
                self.page.on("response", on_response)

                await self.page.click('button[type="submit"]')
                await self.page.wait_for_load_state("networkidle", timeout=15000)

                # 等待第一页API响应
                logger.info("等待第一页API响应...")
                await asyncio.sleep(5)

                # 尝试处理弹窗
                try:
                    await self.page.keyboard.press('Escape')
                    await asyncio.sleep(1)
                except:
                    pass

                # 等待更多数据
                await asyncio.sleep(3)

                first_page_count = len(data_list)
                logger.info(f"第1页完成，获取到 {first_page_count} 条数据")

                # 如果需要获取指定页数据，实现翻页逻辑
                if page > 1:
                    # 清空之前的数据，只保留目标页的数据
                    data_list.clear()
                    await self._navigate_to_page(page)

                # 根据"人想要"数量进行倒序排列
                data_list.sort(key=lambda x: x.get('want_count', 0), reverse=True)

                total_count = len(data_list)
                logger.info(f"搜索完成，总共获取到 {total_count} 条真实数据，已按想要人数排序")

                return {
                    'items': data_list,
                    'total': total_count,
                    'is_real_data': True,
                    'source': 'playwright'
                }

            finally:
                await self.close_browser()

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Playwright 搜索失败: {error_msg}")

            # 检查是否是浏览器安装问题
            if "Executable doesn't exist" in error_msg or "playwright install" in error_msg:
                error_msg = "浏览器未安装。请在Docker容器中运行: playwright install chromium"
            elif "BrowserType.launch" in error_msg:
                error_msg = "浏览器启动失败。请确保Docker容器有足够的权限和资源"

            # 如果 Playwright 失败，返回错误信息
            return {
                'items': [],
                'total': 0,
                'error': f'搜索失败: {error_msg}'
            }

    async def _get_fallback_data(self, keyword: str, page: int, page_size: int) -> Dict[str, Any]:
        """获取备选数据（模拟数据）"""
        logger.info(f"使用备选数据: 关键词='{keyword}', 页码={page}, 每页={page_size}")

        # 模拟搜索延迟
        await asyncio.sleep(0.5)

        # 生成模拟数据
        mock_items = []
        start_index = (page - 1) * page_size

        for i in range(page_size):
            item_index = start_index + i + 1
            mock_items.append({
                'item_id': f'mock_{keyword}_{item_index}',
                'title': f'{keyword}相关商品 #{item_index} [模拟数据]',
                'price': f'{100 + item_index * 10}',
                'seller_name': f'卖家{item_index}',
                'item_url': f'https://www.goofish.com/item?id=mock_{keyword}_{item_index}',
                'publish_time': '2025-07-28',
                'tags': [f'标签{i+1}', f'分类{i+1}'],
                'main_image': f'https://via.placeholder.com/200x200?text={keyword}商品{item_index}',
                'raw_data': {
                    'mock': True,
                    'keyword': keyword,
                    'index': item_index
                }
            })

        # 模拟总数
        total_items = 100 + hash(keyword) % 500

        logger.info(f"备选数据生成完成: 找到{len(mock_items)}个商品，总计{total_items}个")

        return {
            'items': mock_items,
            'total': total_items,
            'is_fallback': True
        }

    async def _parse_real_item(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析真实的闲鱼商品数据"""
        try:
            main_data = await self.safe_get(item_data, "data", "item", "main", "exContent", default={})
            click_params = await self.safe_get(item_data, "data", "item", "main", "clickParam", "args", default={})

            # 解析商品信息
            title = await self.safe_get(main_data, "title", default="未知标题")

            # 价格处理
            price_parts = await self.safe_get(main_data, "price", default=[])
            price = "价格异常"
            if isinstance(price_parts, list):
                price = "".join([str(p.get("text", "")) for p in price_parts if isinstance(p, dict)])
                price = price.replace("当前价", "").strip()

                # 统一价格格式处理
                if price and price != "价格异常":
                    # 先移除所有¥符号，避免重复
                    clean_price = price.replace('¥', '').strip()

                    # 处理万单位的价格
                    if "万" in clean_price:
                        try:
                            numeric_price = clean_price.replace('万', '').strip()
                            price_value = float(numeric_price) * 10000
                            price = f"¥{price_value:.0f}"
                        except:
                            price = f"¥{clean_price}"  # 如果转换失败，保持原样但确保有¥符号
                    else:
                        # 普通价格，确保有¥符号
                        if clean_price and (clean_price[0].isdigit() or clean_price.replace('.', '').isdigit()):
                            price = f"¥{clean_price}"
                        else:
                            price = clean_price if clean_price else "价格异常"

            # 只提取"想要人数"标签
            fish_tags_content = ""
            fish_tags = await self.safe_get(main_data, "fishTags", default={})

            # 遍历所有类型的标签 (r2, r3, r4等)
            for tag_type, tag_data in fish_tags.items():
                if isinstance(tag_data, dict) and "tagList" in tag_data:
                    tag_list = tag_data.get("tagList", [])
                    for tag_item in tag_list:
                        if isinstance(tag_item, dict) and "data" in tag_item:
                            content = tag_item["data"].get("content", "")
                            # 只保留包含"人想要"的标签
                            if content and "人想要" in content:
                                fish_tags_content = content
                                break
                    if fish_tags_content:  # 找到后就退出
                        break

            # 其他字段解析
            area = await self.safe_get(main_data, "area", default="地区未知")
            seller = await self.safe_get(main_data, "userNickName", default="匿名卖家")
            raw_link = await self.safe_get(item_data, "data", "item", "main", "targetUrl", default="")
            image_url = await self.safe_get(main_data, "picUrl", default="")

            # 获取商品ID
            item_id = await self.safe_get(click_params, "item_id", default="未知ID")

            # 处理发布时间
            publish_time = "未知时间"
            publish_timestamp = click_params.get("publishTime", "")
            if publish_timestamp and publish_timestamp.isdigit():
                try:
                    publish_time = datetime.fromtimestamp(
                        int(publish_timestamp)/1000
                    ).strftime("%Y-%m-%d %H:%M")
                except:
                    pass

            # 提取"人想要"的数字用于排序
            want_count = self._extract_want_count(fish_tags_content)

            return {
                "item_id": item_id,
                "title": title,
                "price": price,
                "seller_name": seller,
                "item_url": raw_link.replace("fleamarket://", "https://www.goofish.com/"),
                "main_image": f"https:{image_url}" if image_url and not image_url.startswith("http") else image_url,
                "publish_time": publish_time,
                "tags": [fish_tags_content] if fish_tags_content else [],
                "area": area,
                "want_count": want_count,  # 添加想要人数用于排序
                "raw_data": item_data
            }

        except Exception as e:
            logger.warning(f"解析真实商品数据失败: {str(e)}")
            return None

    def _extract_want_count(self, tags_content: str) -> int:
        """从标签内容中提取"人想要"的数字"""
        try:
            if not tags_content or "人想要" not in tags_content:
                return 0

            # 使用正则表达式提取数字
            import re
            # 匹配类似 "123人想要" 或 "1.2万人想要" 的格式
            pattern = r'(\d+(?:\.\d+)?(?:万)?)\s*人想要'
            match = re.search(pattern, tags_content)

            if match:
                number_str = match.group(1)
                if '万' in number_str:
                    # 处理万单位
                    number = float(number_str.replace('万', '')) * 10000
                    return int(number)
                else:
                    return int(float(number_str))

            return 0
        except Exception as e:
            logger.warning(f"提取想要人数失败: {str(e)}")
            return 0

    async def _navigate_to_page(self, target_page: int):
        """导航到指定页面"""
        try:
            logger.info(f"正在导航到第 {target_page} 页...")

            # 等待页面稳定
            await asyncio.sleep(2)

            # 查找并点击下一页按钮
            next_button_selectors = [
                '.search-page-tiny-arrow-right--oXVFaRao',  # 用户找到的正确选择器
                '[class*="search-page-tiny-arrow-right"]',  # 更通用的版本
                'button[aria-label="下一页"]',
                'button:has-text("下一页")',
                'a:has-text("下一页")',
                '.ant-pagination-next',
                'li.ant-pagination-next a',
                'a[aria-label="下一页"]',
                '[class*="next"]',
                '[class*="pagination-next"]',
                'button[title="下一页"]',
                'a[title="下一页"]'
            ]

            # 从第2页开始点击
            for current_page in range(2, target_page + 1):
                logger.info(f"正在点击到第 {current_page} 页...")

                next_button_found = False
                for selector in next_button_selectors:
                    try:
                        next_button = self.page.locator(selector).first

                        if await next_button.is_visible(timeout=3000):
                            # 检查按钮是否可点击（不是禁用状态）
                            is_disabled = await next_button.get_attribute("disabled")
                            has_disabled_class = await next_button.evaluate("el => el.classList.contains('ant-pagination-disabled') || el.classList.contains('disabled')")

                            if not is_disabled and not has_disabled_class:
                                logger.info(f"找到下一页按钮，正在点击...")

                                # 滚动到按钮位置
                                await next_button.scroll_into_view_if_needed()
                                await asyncio.sleep(1)

                                # 点击下一页
                                await next_button.click()
                                await self.page.wait_for_load_state("networkidle", timeout=15000)

                                # 等待新数据加载
                                await asyncio.sleep(5)

                                logger.info(f"成功导航到第 {current_page} 页")
                                next_button_found = True
                                break

                    except Exception as e:
                        continue

                if not next_button_found:
                    logger.warning(f"无法找到下一页按钮，停止在第 {current_page-1} 页")
                    break

        except Exception as e:
            logger.error(f"导航到第 {target_page} 页失败: {str(e)}")

    async def search_multiple_pages(self, keyword: str, total_pages: int = 1) -> Dict[str, Any]:
        """
        搜索多页闲鱼商品

        Args:
            keyword: 搜索关键词
            total_pages: 总页数

        Returns:
            搜索结果字典，包含所有页面的items列表和总数
        """
        try:
            if not PLAYWRIGHT_AVAILABLE:
                logger.error("Playwright 不可用，无法获取真实数据")
                return {
                    'items': [],
                    'total': 0,
                    'error': 'Playwright 不可用，无法获取真实数据'
                }

            logger.info(f"使用 Playwright 搜索多页闲鱼商品: 关键词='{keyword}', 总页数={total_pages}")

            await self.init_browser()

            # 清空之前的API响应
            self.api_responses = []
            all_data_list = []

            # 设置API响应监听器
            async def on_response(response):
                """处理API响应，解析数据"""
                if "h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search" in response.url:
                    try:
                        # 检查响应状态
                        if response.status != 200:
                            logger.warning(f"API响应状态异常: {response.status}")
                            return

                        # 安全地获取响应内容
                        try:
                            result_json = await response.json()
                        except Exception as json_error:
                            logger.warning(f"无法解析响应JSON: {str(json_error)}")
                            return

                        self.api_responses.append(result_json)
                        logger.info(f"捕获到API响应，URL: {response.url}")

                        items = result_json.get("data", {}).get("resultList", [])
                        logger.info(f"从API获取到 {len(items)} 条原始数据")

                        for item in items:
                            try:
                                parsed_item = await self._parse_real_item(item)
                                if parsed_item:
                                    all_data_list.append(parsed_item)
                            except Exception as parse_error:
                                logger.warning(f"解析单个商品失败: {str(parse_error)}")
                                continue

                    except Exception as e:
                        logger.warning(f"响应处理异常: {str(e)}")

            try:
                logger.info("正在访问闲鱼首页...")
                await self.page.goto("https://www.goofish.com", timeout=30000)
                await self.page.wait_for_load_state("networkidle", timeout=10000)

                logger.info(f"正在搜索关键词: {keyword}")
                await self.page.fill('input[class*="search-input"]', keyword)

                # 注册响应监听
                self.page.on("response", on_response)

                await self.page.click('button[type="submit"]')
                await self.page.wait_for_load_state("networkidle", timeout=15000)

                # 等待第一页API响应
                logger.info("等待第一页API响应...")
                await asyncio.sleep(5)

                # 尝试处理弹窗
                try:
                    await self.page.keyboard.press('Escape')
                    await asyncio.sleep(1)
                except:
                    pass

                # 等待更多数据
                await asyncio.sleep(3)

                first_page_count = len(all_data_list)
                logger.info(f"第1页完成，获取到 {first_page_count} 条数据")

                # 如果需要获取更多页数据
                if total_pages > 1:
                    for page_num in range(2, total_pages + 1):
                        logger.info(f"正在获取第 {page_num} 页数据...")

                        # 等待页面稳定
                        await asyncio.sleep(2)

                        # 查找并点击下一页按钮
                        next_button_found = False
                        next_button_selectors = [
                            '.search-page-tiny-arrow-right--oXVFaRao',
                            '[class*="search-page-tiny-arrow-right"]',
                            'button[aria-label="下一页"]',
                            'button:has-text("下一页")',
                            'a:has-text("下一页")',
                            '.ant-pagination-next',
                            'li.ant-pagination-next a',
                            'a[aria-label="下一页"]'
                        ]

                        for selector in next_button_selectors:
                            try:
                                next_button = self.page.locator(selector).first

                                if await next_button.is_visible(timeout=3000):
                                    # 检查按钮是否可点击
                                    is_disabled = await next_button.get_attribute("disabled")
                                    has_disabled_class = await next_button.evaluate("el => el.classList.contains('ant-pagination-disabled') || el.classList.contains('disabled')")

                                    if not is_disabled and not has_disabled_class:
                                        logger.info(f"找到下一页按钮，正在点击到第 {page_num} 页...")

                                        # 记录点击前的数据量
                                        before_click_count = len(all_data_list)

                                        # 滚动到按钮位置并点击
                                        await next_button.scroll_into_view_if_needed()
                                        await asyncio.sleep(1)
                                        await next_button.click()
                                        await self.page.wait_for_load_state("networkidle", timeout=15000)

                                        # 等待新数据加载
                                        await asyncio.sleep(5)

                                        # 检查是否有新数据
                                        after_click_count = len(all_data_list)
                                        new_items = after_click_count - before_click_count

                                        if new_items > 0:
                                            logger.info(f"第 {page_num} 页成功，新增 {new_items} 条数据")
                                            next_button_found = True
                                            break
                                        else:
                                            logger.warning(f"第 {page_num} 页点击后没有新数据，可能已到最后一页")
                                            next_button_found = False
                                            break

                            except Exception as e:
                                continue

                        if not next_button_found:
                            logger.warning(f"无法获取第 {page_num} 页数据，停止在第 {page_num-1} 页")
                            break

                # 根据"人想要"数量进行倒序排列
                all_data_list.sort(key=lambda x: x.get('want_count', 0), reverse=True)

                total_count = len(all_data_list)
                logger.info(f"多页搜索完成，总共获取到 {total_count} 条真实数据，已按想要人数排序")

                return {
                    'items': all_data_list,
                    'total': total_count,
                    'is_real_data': True,
                    'source': 'playwright'
                }

            finally:
                await self.close_browser()

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Playwright 多页搜索失败: {error_msg}")

            # 检查是否是浏览器安装问题
            if "Executable doesn't exist" in error_msg or "playwright install" in error_msg:
                error_msg = "浏览器未安装。请在Docker容器中运行: playwright install chromium"
            elif "BrowserType.launch" in error_msg:
                error_msg = "浏览器启动失败。请确保Docker容器有足够的权限和资源"

            # 如果 Playwright 失败，返回错误信息
            return {
                'items': [],
                'total': 0,
                'error': f'多页搜索失败: {error_msg}'
            }

    async def _get_multiple_fallback_data(self, keyword: str, total_pages: int) -> Dict[str, Any]:
        """获取多页备选数据（模拟数据）"""
        logger.info(f"使用多页备选数据: 关键词='{keyword}', 总页数={total_pages}")

        # 模拟搜索延迟
        await asyncio.sleep(1)

        # 生成多页模拟数据
        all_mock_items = []

        for page in range(1, total_pages + 1):
            page_size = 20  # 每页20条
            start_index = (page - 1) * page_size

            for i in range(page_size):
                item_index = start_index + i + 1
                all_mock_items.append({
                    'item_id': f'mock_{keyword}_{item_index}',
                    'title': f'{keyword}相关商品 #{item_index} [模拟数据-第{page}页]',
                    'price': f'{100 + item_index * 10}',
                    'seller_name': f'卖家{item_index}',
                    'item_url': f'https://www.goofish.com/item?id=mock_{keyword}_{item_index}',
                    'publish_time': '2025-07-28',
                    'tags': [f'标签{i+1}', f'分类{i+1}'],
                    'main_image': f'https://via.placeholder.com/200x200?text={keyword}商品{item_index}',
                    'raw_data': {
                        'mock': True,
                        'keyword': keyword,
                        'index': item_index,
                        'page': page
                    }
                })

        total_count = len(all_mock_items)
        logger.info(f"多页备选数据生成完成: 找到{total_count}个商品，共{total_pages}页")

        return {
            'items': all_mock_items,
            'total': total_count,
            'is_fallback': True
        }




    async def _parse_item_old(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解析单个商品数据

        Args:
            item_data: 商品原始数据

        Returns:
            解析后的商品信息
        """
        try:
            # 基本信息 - 适配多种可能的字段名
            item_id = (item_data.get('id') or
                      item_data.get('itemId') or
                      item_data.get('item_id') or
                      item_data.get('spuId') or '')

            title = (item_data.get('title') or
                    item_data.get('name') or
                    item_data.get('itemTitle') or
                    item_data.get('subject') or '')

            # 价格处理
            price_raw = (item_data.get('price') or
                        item_data.get('priceText') or
                        item_data.get('currentPrice') or
                        item_data.get('realPrice') or '')

            # 清理价格格式
            if isinstance(price_raw, (int, float)):
                price = str(price_raw)
            elif isinstance(price_raw, str):
                price = price_raw.replace('¥', '').replace('元', '').strip()
            else:
                price = '价格面议'

            # 卖家信息
            seller_info = (item_data.get('seller') or
                          item_data.get('user') or
                          item_data.get('owner') or {})

            seller_name = ''
            if seller_info:
                seller_name = (seller_info.get('nick') or
                              seller_info.get('nickname') or
                              seller_info.get('name') or
                              seller_info.get('userName') or '匿名用户')

            # 商品链接
            if item_id:
                item_url = f"https://www.goofish.com/item?id={item_id}"
            else:
                item_url = item_data.get('url', item_data.get('link', ''))

            # 发布时间
            publish_time = (item_data.get('publishTime') or
                           item_data.get('createTime') or
                           item_data.get('gmtCreate') or
                           item_data.get('time') or '')

            # 格式化时间
            if publish_time and isinstance(publish_time, (int, float)):
                import datetime
                publish_time = datetime.datetime.fromtimestamp(publish_time / 1000).strftime('%Y-%m-%d')

            # 商品标签
            tags = item_data.get('tags', item_data.get('labels', []))
            tag_names = []
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, dict):
                        tag_name = (tag.get('name') or
                                   tag.get('text') or
                                   tag.get('label') or '')
                        if tag_name:
                            tag_names.append(tag_name)
                    elif isinstance(tag, str):
                        tag_names.append(tag)

            # 图片
            images = (item_data.get('images') or
                     item_data.get('pics') or
                     item_data.get('pictures') or
                     item_data.get('imgList') or [])

            main_image = ''
            if images and len(images) > 0:
                if isinstance(images[0], str):
                    main_image = images[0]
                elif isinstance(images[0], dict):
                    main_image = (images[0].get('url') or
                                 images[0].get('src') or
                                 images[0].get('image') or '')

            # 如果没有图片，使用默认占位图
            if not main_image:
                main_image = f'https://via.placeholder.com/200x200?text={title[:10] if title else "商品"}...'
            
            return {
                'item_id': item_id,
                'title': title,
                'price': price,
                'seller_name': seller_name,
                'item_url': item_url,
                'publish_time': publish_time,
                'tags': tag_names,
                'main_image': main_image,
                'raw_data': item_data  # 保留原始数据以备后用
            }
            
        except Exception as e:
            logger.warning(f"解析商品数据失败: {str(e)}")
            return None


# 全局搜索器实例
_searcher = None

async def search_xianyu_items(keyword: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    搜索闲鱼商品的便捷函数

    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页数量

    Returns:
        搜索结果
    """
    global _searcher

    if not _searcher:
        _searcher = XianyuSearcher()

    try:
        return await _searcher.search_items(keyword, page, page_size)
    except Exception as e:
        logger.error(f"搜索商品失败: {str(e)}")
        return {
            'items': [],
            'total': 0,
            'error': str(e)
        }


async def search_multiple_pages_xianyu(keyword: str, total_pages: int = 1) -> Dict[str, Any]:
    """
    搜索多页闲鱼商品的便捷函数

    Args:
        keyword: 搜索关键词
        total_pages: 总页数

    Returns:
        搜索结果
    """
    global _searcher

    if not _searcher:
        _searcher = XianyuSearcher()

    try:
        return await _searcher.search_multiple_pages(keyword, total_pages)
    except Exception as e:
        logger.error(f"多页搜索商品失败: {str(e)}")
        return {
            'items': [],
            'total': 0,
            'error': str(e)
        }

async def close_searcher():
    """关闭搜索器"""
    global _searcher
    if _searcher:
        await _searcher.close_session()
        _searcher = None


async def get_item_detail_from_api(item_id: str) -> Optional[str]:
    """
    从外部API获取商品详情

    Args:
        item_id: 商品ID

    Returns:
        商品详情文本，获取失败返回None
    """
    try:
        # 使用默认的API配置
        api_base_url = 'https://selfapi.zhinianboke.com/api/getItemDetail'
        timeout_seconds = 10

        api_url = f"{api_base_url}/{item_id}"

        logger.info(f"正在从外部API获取商品详情: {item_id}")

        # 使用简单的HTTP请求
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    result = await response.json()

                    # 检查返回状态
                    if result.get('status') == '200' and result.get('data'):
                        item_detail = result['data']
                        logger.info(f"成功获取商品详情: {item_id}, 长度: {len(item_detail)}")
                        return item_detail
                    else:
                        logger.warning(f"API返回状态异常: {result.get('status')}, message: {result.get('message')}")
                        return None
                else:
                    logger.warning(f"API请求失败: HTTP {response.status}")
                    return None

    except asyncio.TimeoutError:
        logger.warning(f"获取商品详情超时: {item_id}")
        return None
    except Exception as e:
        logger.error(f"获取商品详情异常: {item_id}, 错误: {str(e)}")
        return None
