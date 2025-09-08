#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云 DNS 配置管理模块

提供阿里云 DNS API 的配置管理功能，包括认证信息、API 端点、区域配置等。
设计遵循 ChatTool 项目的配置管理模式。
"""

from typing import Optional, Dict, Any

class AliyunDNSConfig:
    """
    阿里云 DNS 配置类
    
    管理阿里云 DNS API 调用所需的各种配置参数，包括认证信息、API 端点、
    区域设置、重试策略等。
    """
    
    def __init__(self, access_key_id: str, access_key_secret: str,
                 region_id: str = "cn-hangzhou",
                 api_base: Optional[str] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 30.0):
        """
        初始化阿里云 DNS 配置
        
        Args:
            access_key_id: 阿里云 Access Key ID
            access_key_secret: 阿里云 Access Key Secret
            region_id: 区域 ID，默认为 cn-hangzhou
            api_base: API 基础 URL，如果为空则根据区域自动生成
            max_retries: 最大重试次数，默认为 3
            retry_delay: 重试延迟时间（秒），默认为 1.0
            timeout: 请求超时时间（秒），默认为 30.0
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region_id = region_id
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        # 设置 API 基础 URL
        self.api_base = api_base or self._get_api_base(region_id)
        
        # API 版本和格式设置
        self.api_version = "2015-01-09"
        self.format = "JSON"
        
        # 签名相关配置
        self.signature_method = "HMAC-SHA1"
        self.signature_version = "1.0"
        
        # 支持的记录类型
        self.supported_record_types = {
            'A': 'IPv4 地址记录',
            'AAAA': 'IPv6 地址记录',
            'CNAME': '别名记录',
            'MX': '邮件交换记录',
            'TXT': '文本记录',
            'NS': '域名服务器记录',
            'SRV': '服务记录',
            'CAA': '证书颁发机构授权记录'
        }
        
        # 支持的解析线路
        self.supported_lines = {
            'default': '默认线路',
            'telecom': '中国电信',
            'unicom': '中国联通',
            'mobile': '中国移动',
            'oversea': '海外线路',
            'edu': '教育网',
            'drpeng': '鹏博士',
            'btvn': '广电网'
        }
    
    def _get_api_base(self, region_id: str) -> str:
        """
        根据区域 ID 获取对应的 API 基础 URL
        
        Args:
            region_id: 区域 ID
            
        Returns:
            API 基础 URL
        """
        # 阿里云 DNS API 端点映射
        regional_endpoints = {
            'cn-hangzhou': 'https://alidns.cn-hangzhou.aliyuncs.com',
            'cn-shanghai': 'https://alidns.cn-shanghai.aliyuncs.com',
            'cn-qingdao': 'https://alidns.cn-qingdao.aliyuncs.com',
            'cn-beijing': 'https://alidns.cn-beijing.aliyuncs.com',
            'cn-shenzhen': 'https://alidns.cn-shenzhen.aliyuncs.com',
            'cn-hongkong': 'https://alidns.cn-hongkong.aliyuncs.com',
            'ap-southeast-1': 'https://alidns.ap-southeast-1.aliyuncs.com',
            'ap-northeast-1': 'https://alidns.ap-northeast-1.aliyuncs.com',
            'eu-central-1': 'https://alidns.eu-central-1.aliyuncs.com',
            'us-west-1': 'https://alidns.us-west-1.aliyuncs.com',
            'us-east-1': 'https://alidns.us-east-1.aliyuncs.com'
        }
        
        return regional_endpoints.get(region_id, 'https://alidns.cn-hangzhou.aliyuncs.com')
    
    def get_headers(self) -> Dict[str, str]:
        """
        获取请求头
        
        Returns:
            HTTP 请求头字典
        """
        return {
            'User-Agent': 'AliyunDNSClient/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    def validate(self) -> bool:
        """
        验证配置的完整性
        
        Returns:
            配置是否有效
        """
        required_fields = [
            'access_key_id',
            'access_key_secret',
            'region_id',
            'api_base'
        ]
        
        for field in required_fields:
            value = getattr(self, field, None)
            if not value:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典格式
        
        Returns:
            配置字典，不包含敏感信息
        """
        return {
            'region_id': self.region_id,
            'api_base': self.api_base,
            'api_version': self.api_version,
            'format': self.format,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'timeout': self.timeout,
            'signature_method': self.signature_method,
            'signature_version': self.signature_version,
            'supported_record_types': self.supported_record_types,
            'supported_lines': self.supported_lines
        }
    
    def __str__(self) -> str:
        """配置对象的字符串表示（不包含敏感信息）"""
        return f"AliyunDNSConfig(region={self.region_id}, api_base={self.api_base})"
    
    def __repr__(self) -> str:
        """配置对象的详细字符串表示"""
        return (f"AliyunDNSConfig(access_key_id={self.access_key_id[:8]}..., "
                f"region_id={self.region_id}, api_base={self.api_base})")


class DNSRecordType:
    """
    DNS 记录类型常量类
    
    提供所有支持的 DNS 记录类型的常量定义，便于代码中使用。
    """
    
    A = 'A'                    # IPv4 地址记录
    AAAA = 'AAAA'              # IPv6 地址记录
    CNAME = 'CNAME'            # 别名记录
    MX = 'MX'                  # 邮件交换记录
    TXT = 'TXT'                # 文本记录
    NS = 'NS'                  # 域名服务器记录
    SRV = 'SRV'                # 服务记录
    CAA = 'CAA'                # 证书颁发机构授权记录
    
    @classmethod
    def all_types(cls) -> list:
        """获取所有支持的记录类型"""
        return [cls.A, cls.AAAA, cls.CNAME, cls.MX, cls.TXT, cls.NS, cls.SRV, cls.CAA]
    
    @classmethod
    def is_valid_type(cls, record_type: str) -> bool:
        """检查记录类型是否有效"""
        return record_type in cls.all_types()


class DNSLineType:
    """
    DNS 解析线路类型常量类
    
    提供所有支持的解析线路的常量定义。
    """
    
    DEFAULT = 'default'        # 默认线路
    TELECOM = 'telecom'        # 中国电信
    UNICOM = 'unicom'          # 中国联通
    MOBILE = 'mobile'          # 中国移动
    OVERSEA = 'oversea'        # 海外线路
    EDU = 'edu'                # 教育网
    DRPENG = 'drpeng'          # 鹏博士
    BTVN = 'btvn'              # 广电网
    
    @classmethod
    def all_lines(cls) -> list:
        """获取所有支持的解析线路"""
        return [cls.DEFAULT, cls.TELECOM, cls.UNICOM, cls.MOBILE, 
                cls.OVERSEA, cls.EDU, cls.DRPENG, cls.BTVN]
    
    @classmethod
    def is_valid_line(cls, line: str) -> bool:
        """检查解析线路是否有效"""
        return line in cls.all_lines()


class AliyunRegion:
    """
    阿里云区域常量类
    
    提供阿里云所有可用区域的常量定义。
    """
    
    # 中国大陆区域
    CN_HANGZHOU = 'cn-hangzhou'        # 华东1（杭州）
    CN_SHANGHAI = 'cn-shanghai'        # 华东2（上海）
    CN_QINGDAO = 'cn-qingdao'          # 华北1（青岛）
    CN_BEIJING = 'cn-beijing'          # 华北2（北京）
    CN_ZHANGJIAKOU = 'cn-zhangjiakou'  # 华北3（张家口）
    CN_HUHEHAOTE = 'cn-huhehaote'      # 华北5（呼和浩特）
    CN_SHENZHEN = 'cn-shenzhen'        # 华南1（深圳）
    CN_CHENGDU = 'cn-chengdu'          # 西南1（成都）
    
    # 香港及海外区域
    CN_HONGKONG = 'cn-hongkong'        # 香港
    AP_SOUTHEAST_1 = 'ap-southeast-1'   # 亚太东南1（新加坡）
    AP_SOUTHEAST_2 = 'ap-southeast-2'   # 亚太东南2（悉尼）
    AP_SOUTHEAST_3 = 'ap-southeast-3'   # 亚太东南3（吉隆坡）
    AP_NORTHEAST_1 = 'ap-northeast-1'   # 亚太东北1（东京）
    EU_CENTRAL_1 = 'eu-central-1'       # 欧洲中部1（法兰克福）
    EU_WEST_1 = 'eu-west-1'             # 欧洲西部1（伦敦）
    US_WEST_1 = 'us-west-1'             # 美国西部1（硅谷）
    US_EAST_1 = 'us-east-1'             # 美国东部1（弗吉尼亚）
    
    @classmethod
    def all_regions(cls) -> list:
        """获取所有支持的区域"""
        return [
            cls.CN_HANGZHOU, cls.CN_SHANGHAI, cls.CN_QINGDAO, cls.CN_BEIJING,
            cls.CN_ZHANGJIAKOU, cls.CN_HUHEHAOTE, cls.CN_SHENZHEN, cls.CN_CHENGDU,
            cls.CN_HONGKONG, cls.AP_SOUTHEAST_1, cls.AP_SOUTHEAST_2, cls.AP_SOUTHEAST_3,
            cls.AP_NORTHEAST_1, cls.EU_CENTRAL_1, cls.EU_WEST_1, cls.US_WEST_1, cls.US_EAST_1
        ]
    
    @classmethod
    def is_valid_region(cls, region: str) -> bool:
        """检查区域是否有效"""
        return region in cls.all_regions()
    
    @classmethod
    def get_mainland_regions(cls) -> list:
        """获取中国大陆区域"""
        return [
            cls.CN_HANGZHOU, cls.CN_SHANGHAI, cls.CN_QINGDAO, cls.CN_BEIJING,
            cls.CN_ZHANGJIAKOU, cls.CN_HUHEHAOTE, cls.CN_SHENZHEN, cls.CN_CHENGDU
        ]
    
    @classmethod
    def get_overseas_regions(cls) -> list:
        """获取海外区域"""
        return [
            cls.CN_HONGKONG, cls.AP_SOUTHEAST_1, cls.AP_SOUTHEAST_2, cls.AP_SOUTHEAST_3,
            cls.AP_NORTHEAST_1, cls.EU_CENTRAL_1, cls.EU_WEST_1, cls.US_WEST_1, cls.US_EAST_1
        ]