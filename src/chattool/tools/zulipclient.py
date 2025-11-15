import json
import logging
from typing import List, Dict, Optional, Any
import os
from chattool.core import HTTPClient, HTTPConfig
from batch_executor import setup_logger
import asyncio

ZULIP_BOT_EMAIL = os.getenv('ZULIP_BOT_EMAIL')
ZULIP_BOT_API_KEY = os.getenv('ZULIP_BOT_API_KEY')
ZULIP_SITE = os.getenv('ZULIP_SITE')

class ZulipConfig(HTTPConfig):
    """Zulip 专用配置类"""
    def __init__(self, site_url: str, bot_email: str, bot_api_key: str):
        # 设置基础 URL 和认证
        super().__init__(
            api_base=site_url.rstrip('/') + "/api/v1",
            timeout=30,
            max_retries=3,
            retry_delay=1
        )
        # 设置基础认证
        import base64
        credentials = base64.b64encode(f"{bot_email}:{bot_api_key}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

class ZulipClient(HTTPClient):
    def __init__(self, 
                 site_url: Optional[str] = None,
                 bot_email: Optional[str] = None,
                 bot_api_key: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """初始化 Zulip 客户端"""
        # 获取配置
        site_url = site_url or ZULIP_SITE
        bot_email = bot_email or ZULIP_BOT_EMAIL
        bot_api_key = bot_api_key or ZULIP_BOT_API_KEY
        
        if not all([site_url, bot_email, bot_api_key]):
            raise ValueError("site_url, bot_email, 和 bot_api_key 不能为空")
        
        # 创建配置并初始化父类
        config = ZulipConfig(site_url, bot_email, bot_api_key)
        super().__init__(config, logger or setup_logger(self.__class__.__name__))

    def _handle_response(self, response) -> Optional[Dict]:
        """处理 Zulip API 响应"""
        try:
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"请求失败: {response.status_code} - {response.url}")
                return None
        except Exception as e:
            self.logger.error(f"解析响应失败: {e}")
            return None

    # === 异步方法 ===
    async def get_channels_async(self) -> List[Dict]:
        """获取频道列表"""
        try:
            response = await self.async_get("/users/me/subscriptions")
            data = self._handle_response(response)
            return data.get("subscriptions", []) if data else []
        except Exception as e:
            self.logger.error(f"获取频道列表失败: {e}")
            return []

    async def get_topics_async(self, stream_id: int) -> List[Dict]:
        """获取话题列表"""
        try:
            response = await self.async_get(f"/users/me/{stream_id}/topics")
            data = self._handle_response(response)
            return data.get("topics", []) if data else []
        except Exception as e:
            self.logger.error(f"获取话题列表失败: {e}")
            return []

    async def get_topic_history_async(self, stream_id: int, topic_name: str, 
                                     batch_size: int = 100, latest: bool = True) -> List[Dict[str, Any]]:
        """获取指定频道和话题的完整消息历史记录"""
        self.logger.info(f"开始获取话题 '{topic_name}' (频道 {stream_id}) 的完整历史...")
        
        # 构建查询条件
        narrow = [
            {"operator": "stream", "operand": stream_id},
            {"operator": "topic", "operand": topic_name}
        ]
        
        all_messages = []
        anchor = "newest"
        request_count = 0
        
        try:
            while True:
                request_count += 1
                self.logger.debug(f"第 {request_count} 次请求: anchor='{anchor}'")
                
                # 构建参数
                params = {
                    "narrow": json.dumps(narrow),
                    "anchor": anchor,
                    "num_before": batch_size,
                    "num_after": 0,
                    "apply_markdown": 'false'
                }
                
                # 使用 HTTPClient 的方法，但需要处理 form data
                response = await self.async_get("/messages", params=params)
                data = self._handle_response(response)
                
                if not data or "result" not in data:
                    self.logger.error(f"获取消息批次 #{request_count} 失败")
                    break
                    
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
        
        except Exception as e:
            self.logger.error(f"获取话题历史失败: {e}")
            return []
        
        self.logger.info(f"已完成话题历史获取：共 {len(all_messages)} 条消息，用了 {request_count} 次请求")
        
        # 按时间顺序排序和去重
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

    async def search_messages_async(self, keyword: str, 
                                   stream_id: Optional[int] = None,
                                   topic_name: Optional[str] = None,
                                   sender_email: Optional[str] = None,
                                   batch_size: int = 100) -> List[Dict]:
        """异步搜索包含关键词的消息
        
        Args:
            keyword: 搜索关键词
            stream_id: 可选，限定在特定频道ID中搜索
            topic_name: 可选，限定在特定话题中搜索
            sender_email: 可选，限定特定发送者
            batch_size: 每次请求获取的消息数量
        
        Returns:
            包含关键词的消息列表
        """
        self.logger.info(f"开始搜索包含关键词 '{keyword}' 的消息...")
        
        # 构建查询条件
        narrow = [{"operator": "search", "operand": keyword}]
        
        # 添加可选的过滤条件
        if stream_id is not None:
            narrow.append({"operator": "stream", "operand": stream_id})
        if topic_name is not None:
            narrow.append({"operator": "topic", "operand": topic_name})
        if sender_email is not None:
            narrow.append({"operator": "sender", "operand": sender_email})
        
        all_messages = []
        anchor = "newest"
        request_count = 0
        
        try:
            while True:
                request_count += 1
                self.logger.debug(f"第 {request_count} 次请求: anchor='{anchor}'")
                
                # 构建参数
                params = {
                    "narrow": json.dumps(narrow),
                    "anchor": anchor,
                    "num_before": batch_size,
                    "num_after": 0,
                    "apply_markdown": 'false'
                }
                
                # 发送请求
                response = await self.async_get("/messages", params=params)
                data = self._handle_response(response)
                
                if not data or "result" not in data:
                    self.logger.error(f"搜索消息批次 #{request_count} 失败")
                    break
                    
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
                if request_count >= 100:
                    self.logger.warning("达到最大请求次数限制，返回可能不完整的结果")
                    break
        
        except Exception as e:
            self.logger.error(f"搜索消息失败: {e}")
            return []
        
        self.logger.info(f"已完成消息搜索：共 {len(all_messages)} 条消息，用了 {request_count} 次请求")
        return all_messages

    # === 同步方法 ===
    def get_channels(self) -> List[Dict]:
        """同步获取频道列表"""
        try:
            response = self.get("/users/me/subscriptions")
            data = self._handle_response(response)
            return data.get("subscriptions", []) if data else []
        except Exception as e:
            self.logger.error(f"获取频道列表失败: {e}")
            return []

    def get_topics(self, stream_id: int) -> List[Dict]:
        """同步获取话题列表"""
        try:
            response = self.get(f"/users/me/{stream_id}/topics")
            data = self._handle_response(response)
            return data.get("topics", []) if data else []
        except Exception as e:
            self.logger.error(f"获取话题列表失败: {e}")
            return []

    def get_topic_history(self, stream_id: int, topic_name: str, 
                         batch_size: int = 100, latest: bool = True) -> List[Dict]:
        """同步获取话题完整历史"""
        # 由于消息历史获取涉及多个异步请求，建议使用异步版本
        # 这里提供一个简化的同步版本
        try:
            # 对于同步版本，我们只获取一批消息作为示例
            narrow = [
                {"operator": "stream", "operand": stream_id},
                {"operator": "topic", "operand": topic_name}
            ]
            
            params = {
                "narrow": json.dumps(narrow),
                "anchor": "newest",
                "num_before": batch_size,
                "num_after": 0,
                "apply_markdown": 'false'
            }
            
            response = self.get("/messages", params=params)
            data = self._handle_response(response)
            
            if data and "messages" in data:
                return data["messages"]
            return []
            
        except Exception as e:
            self.logger.error(f"获取话题历史失败: {e}")
            return []

    def search_messages(self, keyword: str,
                       stream_id: Optional[int] = None,
                       topic_name: Optional[str] = None,
                       sender_email: Optional[str] = None,
                       batch_size: int = 100) -> List[Dict]:
        """同步搜索包含关键词的消息
        
        Args:
            keyword: 搜索关键词
            stream_id: 可选，限定在特定频道ID中搜索
            topic_name: 可选，限定在特定话题中搜索
            sender_email: 可选，限定特定发送者
            batch_size: 每次请求获取的消息数量
        
        Returns:
            包含关键词的消息列表
        """
        self.logger.info(f"开始同步搜索包含关键词 '{keyword}' 的消息...")
        
        # 构建查询条件
        narrow = [{"operator": "search", "operand": keyword}]
        
        # 添加可选的过滤条件
        if stream_id is not None:
            narrow.append({"operator": "stream", "operand": stream_id})
        if topic_name is not None:
            narrow.append({"operator": "topic", "operand": topic_name})
        if sender_email is not None:
            narrow.append({"operator": "sender", "operand": sender_email})
        
        # 构建参数
        params = {
            "narrow": json.dumps(narrow),
            "anchor": "newest",
            "num_before": batch_size,
            "num_after": 0,
            "apply_markdown": 'false'
        }
        
        try:
            # 发送请求
            response = self.get("/messages", params=params)
            data = self._handle_response(response)
            
            if data and "messages" in data:
                return data["messages"]
            return []
            
        except Exception as e:
            self.logger.error(f"同步搜索消息失败: {e}")
            return []