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
            # 为没有状态记录的Cookie设置默认启用状态
            for cookie_id in self.cookies.keys():
                if cookie_id not in self.cookie_status:
                    self.cookie_status[cookie_id] = True
            logger.info(f"从数据库加载了 {len(self.cookies)} 个Cookie、{len(self.keywords)} 组关键字和 {len(self.cookie_status)} 个状态记录")
        except Exception as e:
            logger.error(f"从数据库加载数据失败: {e}")

    # ------------------------ 内部协程 ------------------------
    async def _run_xianyu(self, cookie_id: str, cookie_value: str):
        """在事件循环中启动 XianyuLive.main"""
        from XianyuAutoAsync import XianyuLive  # 延迟导入，避免循环
        try:
            live = XianyuLive(cookie_value, cookie_id=cookie_id)
            await live.main()
        except asyncio.CancelledError:
            logger.info(f"XianyuLive 任务已取消: {cookie_id}")
        except Exception as e:
            logger.error(f"XianyuLive 任务异常({cookie_id}): {e}")

    async def _add_cookie_async(self, cookie_id: str, cookie_value: str):
        if cookie_id in self.tasks:
            raise ValueError("Cookie ID already exists")
        self.cookies[cookie_id] = cookie_value
        # 保存到数据库
        db_manager.save_cookie(cookie_id, cookie_value)
        task = self.loop.create_task(self._run_xianyu(cookie_id, cookie_value))
        self.tasks[cookie_id] = task
        logger.info(f"已启动账号任务: {cookie_id}")

    async def _remove_cookie_async(self, cookie_id: str):
        task = self.tasks.pop(cookie_id, None)
        if task:
            task.cancel()
        self.cookies.pop(cookie_id, None)
        self.keywords.pop(cookie_id, None)
        # 从数据库删除
        db_manager.delete_cookie(cookie_id)
        logger.info(f"已移除账号: {cookie_id}")

    # ------------------------ 对外线程安全接口 ------------------------
    def add_cookie(self, cookie_id: str, cookie_value: str, kw_list: Optional[List[Tuple[str, str]]] = None):
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
            return self.loop.create_task(self._add_cookie_async(cookie_id, cookie_value))
        else:
            fut = asyncio.run_coroutine_threadsafe(self._add_cookie_async(cookie_id, cookie_value), self.loop)
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
    def update_cookie(self, cookie_id: str, new_value: str):
        """替换指定账号的 Cookie 并重启任务"""
        async def _update():
            # 先移除
            if cookie_id in self.tasks:
                await self._remove_cookie_async(cookie_id)
            # 再添加
            await self._add_cookie_async(cookie_id, new_value)

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

        self.cookie_status[cookie_id] = enabled
        # 保存到数据库
        db_manager.save_cookie_status(cookie_id, enabled)
        logger.info(f"更新Cookie状态: {cookie_id} -> {'启用' if enabled else '禁用'}")

    def get_cookie_status(self, cookie_id: str) -> bool:
        """获取Cookie的启用状态"""
        return self.cookie_status.get(cookie_id, True)  # 默认启用

    def get_enabled_cookies(self) -> Dict[str, str]:
        """获取所有启用的Cookie"""
        return {cid: value for cid, value in self.cookies.items()
                if self.cookie_status.get(cid, True)}


# 在 Start.py 中会把此变量赋值为具体实例
manager: Optional[CookieManager] = None 