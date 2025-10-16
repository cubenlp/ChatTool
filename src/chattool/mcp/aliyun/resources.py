#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云DNS MCP资源管理

提供证书目录管理和DNS配置资源访问功能。
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


class CertificateDirectoryManager:
    """证书目录管理器"""
    
    def __init__(self, base_path: str = "/etc/ssl"):
        """
        初始化证书目录管理器
        
        Args:
            base_path: 证书基础路径
        """
        self.base_path = Path(base_path)
        self.cert_dir = self.base_path / "certs"
        self.private_dir = self.base_path / "private"
        self.letsencrypt_dir = Path("/etc/letsencrypt")
    
    def read_directory_structure(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        读取证书目录结构
        
        Args:
            path: 指定路径，默认为证书基础路径
            
        Returns:
            目录结构信息
        """
        try:
            target_path = Path(path) if path else self.base_path
            
            if not target_path.exists():
                return {
                    "error": f"路径不存在: {target_path}",
                    "structure": {}
                }
            
            structure = {
                "path": str(target_path),
                "is_directory": target_path.is_dir(),
                "created_time": datetime.fromtimestamp(target_path.stat().st_ctime).isoformat() if target_path.exists() else None,
                "modified_time": datetime.fromtimestamp(target_path.stat().st_mtime).isoformat() if target_path.exists() else None,
                "contents": []
            }
            
            if target_path.is_dir():
                for item in sorted(target_path.iterdir()):
                    try:
                        item_info = {
                            "name": item.name,
                            "path": str(item),
                            "is_directory": item.is_dir(),
                            "size": item.stat().st_size if item.is_file() else None,
                            "modified_time": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                            "permissions": oct(item.stat().st_mode)[-3:]
                        }
                        
                        # 如果是证书文件，添加证书信息
                        if item.is_file() and item.suffix in ['.crt', '.pem', '.cert']:
                            cert_info = self._get_certificate_info(item)
                            if cert_info:
                                item_info.update(cert_info)
                        
                        structure["contents"].append(item_info)
                    except (OSError, PermissionError) as e:
                        structure["contents"].append({
                            "name": item.name,
                            "error": str(e)
                        })
            
            return structure
            
        except Exception as e:
            return {"error": str(e), "structure": {}}
    
    def read_file_content(self, file_path: str, max_size: int = 10240) -> Dict[str, Any]:
        """
        读取证书文件内容
        
        Args:
            file_path: 文件路径
            max_size: 最大文件大小（字节）
            
        Returns:
            文件内容信息
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {"error": f"文件不存在: {file_path}"}
            
            if not path.is_file():
                return {"error": f"不是文件: {file_path}"}
            
            file_stat = path.stat()
            
            # 检查文件大小
            if file_stat.st_size > max_size:
                return {
                    "error": f"文件过大 ({file_stat.st_size} 字节)，超过限制 ({max_size} 字节)",
                    "size": file_stat.st_size
                }
            
            # 读取文件内容
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # 如果是二进制文件，尝试读取为字节并转换为base64
                import base64
                content = base64.b64encode(path.read_bytes()).decode('ascii')
                return {
                    "path": str(path),
                    "content_type": "binary",
                    "content": content,
                    "size": file_stat.st_size,
                    "encoding": "base64"
                }
            
            # 文本文件
            result = {
                "path": str(path),
                "content_type": "text",
                "content": content,
                "size": file_stat.st_size,
                "encoding": "utf-8",
                "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            }
            
            # 如果是证书文件，添加证书解析信息
            if path.suffix in ['.crt', '.pem', '.cert']:
                cert_info = self._get_certificate_info(path)
                if cert_info:
                    result["certificate_info"] = cert_info
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def write_file_content(self, file_path: str, content: str, 
                          create_dirs: bool = True, backup: bool = True) -> Dict[str, Any]:
        """
        写入证书文件内容
        
        Args:
            file_path: 文件路径
            content: 文件内容
            create_dirs: 是否创建目录
            backup: 是否备份现有文件
            
        Returns:
            操作结果
        """
        try:
            path = Path(file_path)
            
            # 创建父目录
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # 备份现有文件
            if backup and path.exists():
                backup_path = path.with_suffix(path.suffix + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                path.rename(backup_path)
            
            # 写入内容
            path.write_text(content, encoding='utf-8')
            
            # 设置适当的权限
            if 'private' in str(path) or 'key' in path.name.lower():
                path.chmod(0o600)  # 私钥文件，仅所有者可读写
            else:
                path.chmod(0o644)  # 证书文件，所有者可读写，其他人可读
            
            return {
                "success": True,
                "path": str(path),
                "size": path.stat().st_size,
                "message": "文件写入成功"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_certificate_info(self, cert_path: Path) -> Optional[Dict[str, Any]]:
        """
        获取证书信息
        
        Args:
            cert_path: 证书文件路径
            
        Returns:
            证书信息
        """
        try:
            import subprocess
            
            # 使用openssl命令解析证书
            result = subprocess.run([
                "openssl", "x509", "-in", str(cert_path), 
                "-noout", "-text", "-dates", "-subject", "-issuer"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return None
            
            output = result.stdout
            
            # 解析证书信息
            cert_info = {
                "is_certificate": True,
                "raw_output": output
            }
            
            # 提取有效期
            import re
            
            not_before_match = re.search(r'notBefore=(.+)', output)
            not_after_match = re.search(r'notAfter=(.+)', output)
            
            if not_before_match:
                cert_info["valid_from"] = not_before_match.group(1).strip()
            
            if not_after_match:
                cert_info["valid_until"] = not_after_match.group(1).strip()
            
            # 提取主题和颁发者
            subject_match = re.search(r'subject=(.+)', output)
            issuer_match = re.search(r'issuer=(.+)', output)
            
            if subject_match:
                cert_info["subject"] = subject_match.group(1).strip()
            
            if issuer_match:
                cert_info["issuer"] = issuer_match.group(1).strip()
            
            return cert_info
            
        except Exception:
            return None
    
    def list_certificates(self) -> List[Dict[str, Any]]:
        """
        列出所有证书文件
        
        Returns:
            证书文件列表
        """
        certificates = []
        
        # 搜索证书目录
        search_dirs = [
            self.cert_dir,
            self.private_dir,
            self.letsencrypt_dir / "live" if self.letsencrypt_dir.exists() else None
        ]
        
        for search_dir in search_dirs:
            if not search_dir or not search_dir.exists():
                continue
                
            try:
                for cert_file in search_dir.rglob("*.crt"):
                    cert_info = self._get_certificate_info(cert_file)
                    cert_dict = {
                        "path": str(cert_file),
                        "name": cert_file.name,
                        "directory": str(cert_file.parent),
                        "size": cert_file.stat().st_size,
                        "modified_time": datetime.fromtimestamp(cert_file.stat().st_mtime).isoformat()
                    }
                    if cert_info:
                        cert_dict.update(cert_info)
                    certificates.append(cert_dict)
                
                # 也搜索 .pem 文件
                for pem_file in search_dir.rglob("*.pem"):
                    if "cert" in pem_file.name.lower() or "fullchain" in pem_file.name.lower():
                        cert_info = self._get_certificate_info(pem_file)
                        pem_dict = {
                            "path": str(pem_file),
                            "name": pem_file.name,
                            "directory": str(pem_file.parent),
                            "size": pem_file.stat().st_size,
                            "modified_time": datetime.fromtimestamp(pem_file.stat().st_mtime).isoformat()
                        }
                        if cert_info:
                            pem_dict.update(cert_info)
                        certificates.append(pem_dict)
                        
            except Exception as e:
                print(f"搜索证书时出错 {search_dir}: {e}")
        
        return sorted(certificates, key=lambda x: x.get("modified_time", ""))


# 资源管理函数
cert_manager = CertificateDirectoryManager()


def cert_directory_reader(path: Optional[str] = None) -> str:
    """
    读取证书目录结构和文件信息
    
    Args:
        path: 指定路径，默认为 /etc/ssl
        
    Returns:
        目录结构的JSON字符串
    """
    structure = cert_manager.read_directory_structure(path)
    return json.dumps(structure, indent=2, ensure_ascii=False)


def cert_file_content(file_path: str) -> str:
    """
    读取特定证书文件内容
    
    Args:
        file_path: 证书文件路径
        
    Returns:
        文件内容的JSON字符串
    """
    content = cert_manager.read_file_content(file_path)
    return json.dumps(content, indent=2, ensure_ascii=False)


def cert_directory_writer(file_path: str, content: str, 
                         create_dirs: bool = True, backup: bool = True) -> str:
    """
    写入证书文件和更新目录结构
    
    Args:
        file_path: 文件路径
        content: 文件内容
        create_dirs: 是否创建目录
        backup: 是否备份现有文件
        
    Returns:
        操作结果的JSON字符串
    """
    result = cert_manager.write_file_content(
        file_path=file_path,
        content=content,
        create_dirs=create_dirs,
        backup=backup
    )
    return json.dumps(result, indent=2, ensure_ascii=False)


def list_all_certificates() -> str:
    """
    列出系统中的所有证书文件
    
    Returns:
        证书列表的JSON字符串
    """
    certificates = cert_manager.list_certificates()
    return json.dumps({
        "total_count": len(certificates),
        "certificates": certificates
    }, indent=2, ensure_ascii=False)
