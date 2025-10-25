from __future__ import annotations
import asyncio
from typing import Dict, List, Tuple, Optional
from loguru import logger
from db_manager import db_manager

__all__ = ["CookieManager", "manager"]


class CookieManager:
    """管理多账号 Cookie 及其对应的 XianyuLive 任务和关键字"""

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.cookies: Dict[str, str] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.keywords: Dict[str, List[Tuple[str, str]]] = {}
        self.cookie_status: Dict[str, bool] = {}  # 账号启用状态
        self.auto_confirm_settings: Dict[str, bool] = {}  # 自动确认发货设置
        self._load_from_db()

    def _load_from_db(self):
        """从数据库加载所有Cookie、关键字和状态"""
        try:
            # 加载所有Cookie
            self.cookies = db_manager.get_all_cookies()
            # 加载所有关键字
            self.keywords = db_manager.get_all_keywords()
            # 加载所有Cookie状态（默认启用）
            self.cookie_status = db_manager.get_all_cookie_status()
            # 加载所有auto_confirm设置
            self.auto_confirm_settings = {}
            for cookie_id in self.cookies.keys():
                # 为没有状态记录的Cookie设置默认启用状态
                if cookie_id not in self.cookie_status:
                    self.cookie_status[cookie_id] = True
                # 加载auto_confirm设置
                self.auto_confirm_settings[cookie_id] = db_manager.get_auto_confirm(cookie_id)
            logger.info(f"从数据库加载了 {len(self.cookies)} 个Cookie、{len(self.keywords)} 组关键字、{len(self.cookie_status)} 个状态记录和 {len(self.auto_confirm_settings)} 个自动确认设置")
        except Exception as e:
            logger.error(f"从数据库加载数据失败: {e}")

    def reload_from_db(self):
        """重新从数据库加载所有数据（用于备份导入后刷新）"""
        logger.info("重新从数据库加载数据...")
        old_cookies_count = len(self.cookies)
        old_keywords_count = len(self.keywords)

        # 重新加载数据
        self._load_from_db()

        new_cookies_count = len(self.cookies)
        new_keywords_count = len(self.keywords)

        logger.info(f"数据重新加载完成: Cookie {old_cookies_count} -> {new_cookies_count}, 关键字组 {old_keywords_count} -> {new_keywords_count}")
        return True

    # ------------------------ 内部协程 ------------------------
    async def _run_xianyu(self, cookie_id: str, cookie_value: str, user_id: int = None):
        """在事件循环中启动 XianyuLive.main"""
        logger.info(f"【{cookie_id}】_run_xianyu方法开始执行...")

        try:
            logger.info(f"【{cookie_id}】正在导入XianyuLive...")
            from XianyuAutoAsync import XianyuLive  # 延迟导入，避免循环
            logger.info(f"【{cookie_id}】XianyuLive导入成功")

            logger.info(f"【{cookie_id}】开始创建XianyuLive实例...")
            logger.info(f"【{cookie_id}】Cookie值长度: {len(cookie_value)}")
            live = XianyuLive(cookie_value, cookie_id=cookie_id, user_id=user_id)
            logger.info(f"【{cookie_id}】XianyuLive实例创建成功，开始调用main()...")
            await live.main()
        except asyncio.CancelledError:
            logger.info(f"XianyuLive 任务已取消: {cookie_id}")
        except Exception as e:
            logger.error(f"XianyuLive 任务异常({cookie_id}): {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")

    async def _add_cookie_async(self, cookie_id: str, cookie_value: str, user_id: int = None):
        if cookie_id in self.tasks:
            raise ValueError("Cookie ID already exists")
        self.cookies[cookie_id] = cookie_value
        # 保存到数据库，如果没有指定user_id，则保持原有绑定关系
        db_manager.save_cookie(cookie_id, cookie_value, user_id)

        # 获取实际保存的user_id（如果没有指定，数据库会返回实际的user_id）
        actual_user_id = user_id
        if actual_user_id is None:
            # 从数据库获取Cookie对应的user_id
            cookie_info = db_manager.get_cookie_details(cookie_id)
            if cookie_info:
                actual_user_id = cookie_info.get('user_id')

        task = self.loop.create_task(self._run_xianyu(cookie_id, cookie_value, actual_user_id))
        self.tasks[cookie_id] = task
        logger.info(f"已启动账号任务: {cookie_id} (用户ID: {actual_user_id})")

    async def _remove_cookie_async(self, cookie_id: str):
        task = self.tasks.pop(cookie_id, None)
        if task:
            task.cancel()
            try:
                # 等待任务完全清理，确保资源释放
                await task
            except asyncio.CancelledError:
                # 任务被取消是预期行为
                pass
            except Exception as e:
                logger.error(f"等待任务清理时出错: {cookie_id}, {e}")
        
        self.cookies.pop(cookie_id, None)
        self.keywords.pop(cookie_id, None)
        # 从数据库删除
        db_manager.delete_cookie(cookie_id)
        logger.info(f"已移除账号: {cookie_id}")

    # ------------------------ 对外线程安全接口 ------------------------
    def add_cookie(self, cookie_id: str, cookie_value: str, kw_list: Optional[List[Tuple[str, str]]] = None, user_id: int = None):
        """线程安全新增 Cookie 并启动任务"""
        if kw_list is not None:
            self.keywords[cookie_id] = kw_list
        else:
            self.keywords.setdefault(cookie_id, [])
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop and current_loop == self.loop:
            # 同一事件循环中，直接调度
            return self.loop.create_task(self._add_cookie_async(cookie_id, cookie_value, user_id))
        else:
            fut = asyncio.run_coroutine_threadsafe(self._add_cookie_async(cookie_id, cookie_value, user_id), self.loop)
            return fut.result()

    def remove_cookie(self, cookie_id: str):
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop and current_loop == self.loop:
            return self.loop.create_task(self._remove_cookie_async(cookie_id))
        else:
            fut = asyncio.run_coroutine_threadsafe(self._remove_cookie_async(cookie_id), self.loop)
            return fut.result()

    # 更新 Cookie 值
    def update_cookie(self, cookie_id: str, new_value: str, save_to_db: bool = True):
        """替换指定账号的 Cookie 并重启任务
        
        Args:
            cookie_id: Cookie ID
            new_value: 新的Cookie值
            save_to_db: 是否保存到数据库（默认True）。当API层已经更新数据库时应设为False，避免覆盖其他字段
        """
        async def _update():
            # 获取原有的user_id和关键词
            original_user_id = None
            original_keywords = []
            original_status = True

            cookie_info = db_manager.get_cookie_details(cookie_id)
            if cookie_info:
                original_user_id = cookie_info.get('user_id')

            # 保存原有的关键词和状态
            if cookie_id in self.keywords:
                original_keywords = self.keywords[cookie_id].copy()
            if cookie_id in self.cookie_status:
                original_status = self.cookie_status[cookie_id]

            # 先移除任务（但不删除数据库记录）
            task = self.tasks.pop(cookie_id, None)
            if task:
                task.cancel()
                try:
                    # 等待任务完全清理，确保资源释放
                    await task
                except asyncio.CancelledError:
                    # 任务被取消是预期行为
                    pass
                except Exception as e:
                    logger.error(f"等待任务清理时出错: {cookie_id}, {e}")

            # 更新Cookie值
            self.cookies[cookie_id] = new_value
            
            # 只有在需要时才保存到数据库（避免覆盖其他字段如pause_duration、remark等）
            if save_to_db:
                db_manager.save_cookie(cookie_id, new_value, original_user_id)

            # 恢复关键词和状态
            self.keywords[cookie_id] = original_keywords
            self.cookie_status[cookie_id] = original_status

            # 重新启动任务
            task = self.loop.create_task(self._run_xianyu(cookie_id, new_value, original_user_id))
            self.tasks[cookie_id] = task

            logger.info(f"已更新Cookie并重启任务: {cookie_id} (用户ID: {original_user_id}, 关键词: {len(original_keywords)}条)")

        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop and current_loop == self.loop:
            return self.loop.create_task(_update())
        else:
            fut = asyncio.run_coroutine_threadsafe(_update(), self.loop)
            return fut.result()

    def update_keywords(self, cookie_id: str, kw_list: List[Tuple[str, str]]):
        """线程安全更新关键字"""
        self.keywords[cookie_id] = kw_list
        # 保存到数据库
        db_manager.save_keywords(cookie_id, kw_list)
        logger.info(f"更新关键字: {cookie_id} -> {len(kw_list)} 条")

    # 查询接口
    def list_cookies(self):
        return list(self.cookies.keys())

    def get_keywords(self, cookie_id: str) -> List[Tuple[str, str]]:
        return self.keywords.get(cookie_id, [])

    def update_cookie_status(self, cookie_id: str, enabled: bool):
        """更新Cookie的启用/禁用状态"""
        if cookie_id not in self.cookies:
            raise ValueError(f"Cookie ID {cookie_id} 不存在")

        old_status = self.cookie_status.get(cookie_id, True)
        self.cookie_status[cookie_id] = enabled
        # 保存到数据库
        db_manager.save_cookie_status(cookie_id, enabled)
        logger.info(f"更新Cookie状态: {cookie_id} -> {'启用' if enabled else '禁用'}")

        # 如果状态发生变化，需要启动或停止任务
        if old_status != enabled:
            if enabled:
                # 启用账号：启动任务
                self._start_cookie_task(cookie_id)
            else:
                # 禁用账号：停止任务
                self._stop_cookie_task(cookie_id)

    def get_cookie_status(self, cookie_id: str) -> bool:
        """获取Cookie的启用状态"""
        return self.cookie_status.get(cookie_id, True)  # 默认启用

    def get_enabled_cookies(self) -> Dict[str, str]:
        """获取所有启用的Cookie"""
        return {cid: value for cid, value in self.cookies.items()
                if self.cookie_status.get(cid, True)}

    def _start_cookie_task(self, cookie_id: str):
        """启动指定Cookie的任务"""
        if cookie_id in self.tasks:
            logger.warning(f"Cookie任务已存在，跳过启动: {cookie_id}")
            return

        cookie_value = self.cookies.get(cookie_id)
        if not cookie_value:
            logger.error(f"Cookie值不存在，无法启动任务: {cookie_id}")
            return

        try:
            # 获取Cookie对应的user_id
            cookie_info = db_manager.get_cookie_details(cookie_id)
            user_id = cookie_info.get('user_id') if cookie_info else None

            # 使用异步方式启动任务
            if hasattr(self.loop, 'is_running') and self.loop.is_running():
                # 事件循环正在运行，使用run_coroutine_threadsafe
                fut = asyncio.run_coroutine_threadsafe(
                    self._add_cookie_async(cookie_id, cookie_value, user_id),
                    self.loop
                )
                fut.result(timeout=5)  # 等待最多5秒
            else:
                # 事件循环未运行，直接创建任务
                task = self.loop.create_task(self._run_xianyu(cookie_id, cookie_value, user_id))
                self.tasks[cookie_id] = task

            logger.info(f"成功启动Cookie任务: {cookie_id}")
        except Exception as e:
            logger.error(f"启动Cookie任务失败: {cookie_id}, {e}")

    def _stop_cookie_task(self, cookie_id: str):
        """停止指定Cookie的任务"""
        if cookie_id not in self.tasks:
            logger.warning(f"Cookie任务不存在，跳过停止: {cookie_id}")
            return

        async def _stop_task_async():
            """异步停止任务并等待清理"""
            try:
                task = self.tasks[cookie_id]
                if not task.done():
                    task.cancel()
                    try:
                        # 等待任务完全清理，确保资源释放
                        await task
                    except asyncio.CancelledError:
                        # 任务被取消是预期行为
                        pass
                    except Exception as e:
                        logger.error(f"等待任务清理时出错: {cookie_id}, {e}")
                    logger.info(f"已取消Cookie任务: {cookie_id}")
                del self.tasks[cookie_id]
                logger.info(f"成功停止Cookie任务: {cookie_id}")
            except Exception as e:
                logger.error(f"停止Cookie任务失败: {cookie_id}, {e}")

        try:
            # 在事件循环中执行异步停止
            if hasattr(self.loop, 'is_running') and self.loop.is_running():
                fut = asyncio.run_coroutine_threadsafe(_stop_task_async(), self.loop)
                fut.result(timeout=10)  # 等待最多10秒
            else:
                logger.warning(f"事件循环未运行，无法正常等待任务清理: {cookie_id}")
                # 直接取消任务（非最佳方案）
                task = self.tasks[cookie_id]
                if not task.done():
                    task.cancel()
                del self.tasks[cookie_id]
        except Exception as e:
            logger.error(f"停止Cookie任务失败: {cookie_id}, {e}")

    def update_auto_confirm_setting(self, cookie_id: str, auto_confirm: bool):
        """实时更新账号的自动确认发货设置"""
        try:
            # 更新内存中的设置
            self.auto_confirm_settings[cookie_id] = auto_confirm
            logger.info(f"更新账号 {cookie_id} 自动确认发货设置: {'开启' if auto_confirm else '关闭'}")

            # 如果账号正在运行，通知XianyuLive实例更新设置
            if cookie_id in self.tasks and not self.tasks[cookie_id].done():
                # 这里可以通过某种方式通知正在运行的XianyuLive实例
                # 由于XianyuLive会从数据库读取设置，所以数据库已经更新就足够了
                logger.info(f"账号 {cookie_id} 正在运行，自动确认发货设置已实时生效")
        except Exception as e:
            logger.error(f"更新自动确认发货设置失败: {cookie_id}, {e}")

    def get_auto_confirm_setting(self, cookie_id: str) -> bool:
        """获取账号的自动确认发货设置"""
        return self.auto_confirm_settings.get(cookie_id, True)  # 默认开启


# 在 Start.py 中会把此变量赋值为具体实例
manager: Optional[CookieManager] = None 