import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Optional, Any
from chattool.custom_logger import setup_logger
import os

ZULIP_BOT_EMAIL = os.getenv('ZULIP_BOT_EMAIL')
ZULIP_BOT_API_KEY = os.getenv('ZULIP_BOT_API_KEY')
ZULIP_SITE = os.getenv('ZULIP_SITE')

class ZulipClient:
    def __init__(self, 
                 site_url: Optional[str]=None,
                 bot_email: Optional[str]=None,
                 bot_api_key: Optional[str]=None,
                 logger: Optional[logging.Logger] = None):
        """初始化 Zulip 客户端"""
        if site_url is None:
            site_url = ZULIP_SITE
        if bot_email is None:
            bot_email = ZULIP_BOT_EMAIL
        if bot_api_key is None:
            bot_api_key = ZULIP_BOT_API_KEY
        
        if not all([site_url, bot_email, bot_api_key]):
            raise ValueError("site_url, bot_email, 和 bot_api_key 不能为空")
        
        self.base_url = site_url.rstrip('/') + "/api/v1"
        self._auth = aiohttp.BasicAuth(login=bot_email, password=bot_api_key)
        self.logger = logger or setup_logger(self.__class__.__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        self._closed = False  # 添加状态标记

    async def __aenter__(self):
        """进入异步上下文，创建并存储 aiohttp session"""
        if self._closed:
            raise RuntimeError("Client has been closed and cannot be reused")
            
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self.logger.info("Created new aiohttp session")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出异步上下文，关闭 aiohttp session"""
        await self.close()

    async def close(self):
        """显式关闭客户端"""
        if self._session and not self._session.closed:
            await self._session.close()
            self.logger.info("Closed aiohttp session")
        self._session = None
        self._closed = True

    def shutdown(self):
        """同步方法关闭客户端"""
        if not self._closed:
            self._run_async(self.close())

    async def _ensure_session(self):
        """确保 session 可用"""
        if self._closed:
            raise RuntimeError("Client has been closed and cannot be reused")
            
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self.logger.info("Created new aiohttp session")
        return self._session

    async def _request(self, method: str, endpoint: str, 
                      params: Optional[Dict] = None, 
                      data: Optional[Dict] = None) -> Optional[Dict]:
        """基础请求方法"""
        if self._closed:
            raise RuntimeError("Client has been closed and cannot be reused")
            
        session = await self._ensure_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.request(method, url, params=params, 
                                     data=data, auth=self._auth) as resp:
                if resp.status == 200:
                    return await resp.json()
                self.logger.warning(f"请求失败: {resp.status} - {url}")
                return None
        except Exception as e:
            self.logger.error(f"请求异常: {e}")
            return None

    def __del__(self):
        """析构函数"""
        if not self._closed:
            self.shutdown()

    def _run_async(self, coro):
        """运行异步代码的同步包装器"""
        try:
            asyncio.get_running_loop()
            raise RuntimeError("不能在异步环境中调用同步方法")
        except RuntimeError:
            return asyncio.run(coro)

    async def _get_messages_batch(self, narrow: List[Dict], 
                                anchor: str, 
                                batch_size: int = 100) -> Optional[Dict]:
        """获取一批消息的通用方法"""
        params = {
            "narrow": json.dumps(narrow),
            "anchor": anchor,
            "num_before": batch_size,
            "num_after": 0
        }
        return await self._request("GET", "/messages", params=params)

    # === 异步公共接口 ===
    async def get_channels_async(self) -> List[Dict]:
        """获取频道列表"""
        data = await self._request("GET", "/users/me/subscriptions")
        return data.get("subscriptions", []) if data else []

    async def get_topics_async(self, stream_id: int) -> List[Dict]:
        """获取话题列表"""
        data = await self._request("GET", f"/users/me/{stream_id}/topics")
        return data.get("topics", []) if data else []

    async def get_topic_history_async(self, stream_id: int, topic_name: str, 
                          batch_size: int = 100, latest:bool=True) -> List[Dict[str, Any]]:
        """
        获取指定频道和话题的完整消息历史记录。
    
        Args:
            stream_id: 频道ID
            topic_name: 话题名称
            batch_size: 每次请求获取的消息数量，建议不超过1000
    
        Returns:
            List[Dict]: 按时间顺序（从旧到新）排列的所有消息列表
        """
        self.logger.info(f"开始获取话题 '{topic_name}' (频道 {stream_id}) 的完整历史...")
        
        # 构建查询条件
        narrow = [
            {"operator": "stream", "operand": stream_id},
            {"operator": "topic", "operand": topic_name}
        ]
        
        all_messages = []
        anchor = "newest"
        request_count = 0
        
        while True:
            request_count += 1
            self.logger.debug(f"第 {request_count} 次请求: anchor='{anchor}'")
            
            # 使用基础请求方法获取数据
            params = {
                "narrow": json.dumps(narrow),
                "anchor": anchor,
                "num_before": batch_size,
                "num_after": 0,
                "apply_markdown": 'false'
            }
            
            data = await self._request("GET", "/messages", params=params)
            
            if not data or "result" not in data:
                self.logger.error(f"获取消息批次 #{request_count} 失败")
                return []
                
            messages = data.get("messages", [])
            if not messages:
                self.logger.debug("收到空消息批次，假定已达到最早消息")
                break
                
            # 将新消息添加到列表前面
            all_messages = messages + all_messages
            
            # 检查是否到达最早消息
            if data.get("found_oldest", False):
                self.logger.debug("已确认达到最早消息")
                break
                
            # 更新锚点为当前批次最早消息的ID
            anchor = str(messages[0]["id"])
            
            # 添加请求延迟
            await asyncio.sleep(0.5)
            
            # 安全检查：限制最大请求次数
            if request_count >= 1000:
                self.logger.warning("达到最大请求次数限制，返回可能不完整的结果")
                break
        
        self.logger.info(f"已完成话题历史获取：共 {len(all_messages)} 条消息，用了 {request_count} 次请求")
        
        # 按时间顺序排序
        messages = sorted(all_messages, key=lambda x: x["id"])
        if latest:
            msgs, msg_ids = [], set()
            for msg in messages:
                msg_id = msg['id']
                if msg_id in msg_ids:
                    msgs[-1] = msg
                else:
                    msg_ids.add(msg_id)
                    msgs.append(msg)
            self.logger.info(f"去重后：共 {len(msgs)} 条消息")
            return msgs
        else:
            return messages

    # === 同步公共接口 ===
    def get_channels(self) -> List[Dict]:
        """同步获取频道列表"""
        return self._run_async(self.get_channels_async())

    def get_topics(self, stream_id: int) -> List[Dict]:
        """同步获取话题列表"""
        return self._run_async(self.get_topics_async(stream_id))

    def get_topic_history(self, stream_id: int, topic_name: str, 
                         batch_size: int = 100, latest:bool=True) -> List[Dict]:
        """同步获取话题完整历史"""
        return self._run_async(
            self.get_topic_history_async(stream_id, topic_name, batch_size, latest)
        )