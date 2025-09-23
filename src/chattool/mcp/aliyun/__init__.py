"""阿里云 DNS 管理工具

阿里云 DNS 工具和 FastMCP 框架构建的完整 MCP 服务。
"""
from .config import validate_environment, get_system_info, config_manager
from .utils import format_dns_record, format_dns_records_table, validate_ip_address, check_prerequisites
from .prompts import (
    chinese_dns_management_guide, english_dns_management_guide, japanese_dns_management_guide,
    dns_troubleshooting_guide, dns_configuration_template
)
from .resources import list_all_certificates, cert_directory_reader

__all__ = [
    'validate_environment',
    'get_system_info',
    'config_manager',
    'format_dns_record',
    'format_dns_records_table',
    'validate_ip_address',
    'check_prerequisites',
    'chinese_dns_management_guide',
    'english_dns_management_guide',
    'japanese_dns_management_guide',
    'dns_troubleshooting_guide',
    'dns_configuration_template',
    'list_all_certificates',
    'cert_directory_reader'
]
