# Response class for Chattool
from typing import Dict, Any, Union, Optional
import json

class ChatResponse:
    """Chat completion 响应包装类"""
    
    def __init__(self, response: Union[Dict, Any]) -> None:
        if isinstance(response, Dict):
            self.response = response
            self._raw_response = None
        else:
            self._raw_response = response
            self.response = response.json() if hasattr(response, 'json') else response
        
    def is_valid(self) -> bool:
        """检查响应是否有效"""
        return 'error' not in self.response
    
    def is_stream(self) -> bool:
        """检查是否为流式响应"""
        return self.response.get('object') == 'chat.completion.chunk'
    
    # === 基础属性 ===
    @property
    def id(self) -> Optional[str]:
        return self.response.get('id')
    
    @property
    def model(self) -> Optional[str]:
        return self.response.get('model')
    
    @property
    def created(self) -> Optional[int]:
        return self.response.get('created')
    
    @property
    def object(self) -> Optional[str]:
        return self.response.get('object')
    
    # === 使用统计 ===
    @property
    def usage(self) -> Optional[Dict]:
        """Token 使用统计"""
        return self.response.get('usage')
    
    @property
    def total_tokens(self) -> int:
        """总 token 数"""
        return self.usage.get('total_tokens', 0) if self.usage else 0
    
    @property
    def prompt_tokens(self) -> int:
        """提示 token 数"""
        return self.usage.get('prompt_tokens', 0) if self.usage else 0
    
    @property
    def completion_tokens(self) -> int:
        """完成 token 数"""
        return self.usage.get('completion_tokens', 0) if self.usage else 0
    
    # === 消息内容 ===
    @property
    def choices(self) -> list:
        """选择列表"""
        return self.response.get('choices', [])
    
    @property
    def message(self) -> Optional[Dict]:
        """消息内容"""
        if self.choices:
            return self.choices[0].get('message')
        return None
    
    @property
    def content(self) -> str:
        """响应内容"""
        if self.message:
            return self.message.get('content', '')
        return ''
    
    @property
    def role(self) -> Optional[str]:
        """消息角色"""
        if self.message:
            return self.message.get('role')
        return None
    
    @property
    def finish_reason(self) -> Optional[str]:
        """完成原因"""
        if self.choices:
            return self.choices[0].get('finish_reason')
        return None
    
    # === 流式响应专用 ===
    @property
    def delta(self) -> Optional[Dict]:
        """流式响应的 delta"""
        if self.choices:
            return self.choices[0].get('delta')
        return None
    
    @property
    def delta_content(self) -> str:
        """流式响应的内容"""
        if self.delta:
            return self.delta.get('content', '')
        return ''
    
    # === 错误处理 ===
    @property
    def error(self) -> Optional[Dict]:
        """错误信息"""
        return self.response.get('error')
    
    @property
    def error_message(self) -> Optional[str]:
        """错误消息"""
        return self.error.get('message') if self.error else None
    
    @property
    def error_type(self) -> Optional[str]:
        """错误类型"""
        return self.error.get('type') if self.error else None
    
    @property
    def error_code(self) -> Optional[str]:
        """错误代码"""
        return self.error.get('code') if self.error else None
    
    # === 调试信息 ===
    def get_debug_info(self) -> Dict[str, Any]:
        """获取调试信息"""
        return {
            "id": self.id,
            "model": self.model,
            "created": self.created,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "is_valid": self.is_valid(),
            "is_stream": self.is_stream()
        }
    
    def print_debug_info(self):
        """打印调试信息"""
        info = self.get_debug_info()
        print("=== Response Debug Info ===")
        for key, value in info.items():
            print(f"{key}: {value}")
        print("=" * 27)
    
    # === 魔术方法 ===
    def __repr__(self) -> str:
        if self.is_valid():
            return f"<ChatResponse: {self.finish_reason}, tokens: {self.total_tokens}>"
        else:
            return f"<ChatResponse: ERROR - {self.error_message}>"
    
    def __str__(self) -> str:
        return self.content
    
    def __getitem__(self, key):
        return self.response[key]
    
    def __contains__(self, key):
        return key in self.response

# 为了向后兼容，保留 Resp 类
Resp = ChatResponse