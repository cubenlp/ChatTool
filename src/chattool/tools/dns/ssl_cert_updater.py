#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL证书自动更新工具 - 基于Let's Encrypt和阿里云DNS

使用Let's Encrypt的DNS-01挑战验证方式自动申请和更新SSL证书。
支持多域名，自动管理DNS TXT记录，生成nginx可用的证书文件。
"""

import os
import time
import click
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from pathlib import Path
import subprocess
import tempfile
import shutil
from batch_executor import setup_logger
from .utils import create_dns_client, DNSClientType

# 证书相关配置
CERT_DIR = "/etc/ssl/certs"              # 证书存储目录
PRIVATE_KEY_DIR = "/etc/ssl/private"     # 私钥存储目录
LOG_FILE = "ssl_cert_updater.log"       # 日志文件
ACME_CHALLENGE_TTL = 120                 # DNS挑战记录TTL
CHALLENGE_WAIT_TIME = 60                 # 等待DNS传播时间
CERT_RENEWAL_DAYS = 30                   # 证书续期提前天数

class SSLCertUpdater:
    """SSL证书自动更新器"""
    
    def __init__(self, 
                 domains: List[str],
                 email: str,
                 cert_dir: str = CERT_DIR,
                 private_key_dir: str = PRIVATE_KEY_DIR,
                 staging: bool = False,
                 logger=None,
                 dns_type: Union[DNSClientType, str]='aliyun',
                 **dns_client_kwargs
        ):
        """
        初始化SSL证书更新器
        
        Args:
            domains: 域名列表
            email: Let's Encrypt账户邮箱
            cert_dir: 证书存储目录
            private_key_dir: 私钥存储目录
            staging: 是否使用Let's Encrypt测试环境
            logger: 日志记录器
            dns_type: DNS客户端类型
            dns_client_kwargs: DNS客户端初始化参数
        """
        self.domains = domains
        self.email = email
        self.cert_dir = Path(cert_dir)
        self.private_key_dir = Path(private_key_dir)
        self.staging = staging
        self.logger = logger or setup_logger(__name__, log_file=LOG_FILE)
        
        # 初始化DNS客户端
        self.dns_client = create_dns_client(dns_type, logger=self.logger, **dns_client_kwargs)
        
        # 创建目录
        self.cert_dir.mkdir(parents=True, exist_ok=True)
        self.private_key_dir.mkdir(parents=True, exist_ok=True)
        
        # Let's Encrypt服务器URL
        self.acme_server = (
            "https://acme-staging-v02.api.letsencrypt.org/directory" if staging
            else "https://acme-v02.api.letsencrypt.org/directory"
        )
        
        self.logger.info(f"SSL证书更新器初始化完成")
        self.logger.info(f"域名: {', '.join(self.domains)}")
        self.logger.info(f"邮箱: {self.email}")
        self.logger.info(f"证书目录: {self.cert_dir}")
        self.logger.info(f"私钥目录: {self.private_key_dir}")
        self.logger.info(f"环境: {'测试' if staging else '生产'}")
    
    def check_cert_expiry(self, domain: str) -> Optional[datetime]:
        """
        检查证书过期时间
        
        Args:
            domain: 域名
            
        Returns:
            证书过期时间，如果证书不存在返回None
        """
        cert_file = self.cert_dir / f"{domain}.crt"
        if not cert_file.exists():
            return None
            
        try:
            result = subprocess.run([
                "openssl", "x509", "-in", str(cert_file), 
                "-noout", "-enddate"
            ], capture_output=True, text=True, check=True)
            
            # 解析日期格式: notAfter=Dec 30 23:59:59 2024 GMT
            date_str = result.stdout.strip().split('=')[1]
            expiry_date = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
            return expiry_date
            
        except (subprocess.CalledProcessError, ValueError, IndexError) as e:
            self.logger.warning(f"无法解析证书过期时间 {domain}: {e}")
            return None
    
    def needs_renewal(self, domain: str) -> bool:
        """
        检查证书是否需要续期
        
        Args:
            domain: 域名
            
        Returns:
            是否需要续期
        """
        expiry_date = self.check_cert_expiry(domain)
        if expiry_date is None:
            self.logger.info(f"域名 {domain} 证书不存在，需要申请")
            return True
            
        days_until_expiry = (expiry_date - datetime.now()).days
        self.logger.info(f"域名 {domain} 证书将在 {days_until_expiry} 天后过期")
        
        if days_until_expiry <= CERT_RENEWAL_DAYS:
            self.logger.info(f"域名 {domain} 证书需要续期")
            return True
        else:
            self.logger.info(f"域名 {domain} 证书暂不需要续期")
            return False
    
    def extract_domain_from_fqdn(self, fqdn: str) -> str:
        """
        从FQDN中提取主域名
        
        Args:
            fqdn: 完整域名
            
        Returns:
            主域名
        """
        parts = fqdn.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return fqdn
    
    async def create_dns_challenge(self, domain: str, challenge_token: str) -> bool:
        """
        创建DNS挑战记录
        
        Args:
            domain: 域名
            challenge_token: 挑战令牌
            
        Returns:
            是否创建成功
        """
        try:
            # 提取主域名
            main_domain = self.extract_domain_from_fqdn(domain)
            challenge_name = f"_acme-challenge.{domain}"
            
            # 如果是子域名，需要调整记录名
            if domain != main_domain:
                subdomain_part = domain.replace(f".{main_domain}", "")
                rr = f"_acme-challenge.{subdomain_part}"
            else:
                rr = "_acme-challenge"
            
            self.logger.info(f"创建DNS挑战记录: {rr}.{main_domain} TXT {challenge_token}")
            
            # 删除可能存在的旧记录
            self.dns_client.delete_record_value(main_domain, rr, "TXT")
            await asyncio.sleep(2)
            
            # 创建新的TXT记录
            record_id = self.dns_client.add_domain_record(
                domain_name=main_domain,
                rr=rr,
                type_="TXT",
                value=challenge_token,
                ttl=ACME_CHALLENGE_TTL
            )
            
            if record_id:
                self.logger.info(f"DNS挑战记录创建成功: {record_id}")
                return True
            else:
                self.logger.error(f"DNS挑战记录创建失败")
                return False
                
        except Exception as e:
            self.logger.error(f"创建DNS挑战记录时发生异常: {e}")
            return False
    
    async def cleanup_dns_challenge(self, domain: str) -> bool:
        """
        清理DNS挑战记录
        
        Args:
            domain: 域名
            
        Returns:
            是否清理成功
        """
        try:
            # 提取主域名
            main_domain = self.extract_domain_from_fqdn(domain)
            
            # 如果是子域名，需要调整记录名
            if domain != main_domain:
                subdomain_part = domain.replace(f".{main_domain}", "")
                rr = f"_acme-challenge.{subdomain_part}"
            else:
                rr = "_acme-challenge"
            
            self.logger.info(f"清理DNS挑战记录: {rr}.{main_domain}")
            
            # 删除TXT记录
            success = self.dns_client.delete_record_value(main_domain, rr, "TXT")
            
            if success:
                self.logger.info(f"DNS挑战记录清理成功")
            else:
                self.logger.warning(f"DNS挑战记录清理失败")
                
            return success
            
        except Exception as e:
            self.logger.error(f"清理DNS挑战记录时发生异常: {e}")
            return False
    
    def run_certbot(self, domains: List[str]) -> bool:
        """
        运行certbot申请证书
        
        Args:
            domains: 域名列表
            
        Returns:
            是否申请成功
        """
        try:
            # 构建certbot命令
            cmd = [
                "certbot", "certonly",
                "--manual",
                "--preferred-challenges", "dns",
                "--manual-auth-hook", self._get_auth_hook_script(),
                "--manual-cleanup-hook", self._get_cleanup_hook_script(),
                "--server", self.acme_server,
                "--email", self.email,
                "--agree-tos",
                "--non-interactive",
                "--cert-path", str(self.cert_dir),
                "--key-path", str(self.private_key_dir)
            ]
            
            # 添加域名
            for domain in domains:
                cmd.extend(["-d", domain])
            
            self.logger.info(f"运行certbot命令: {' '.join(cmd)}")
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("证书申请成功")
                return True
            else:
                self.logger.error(f"证书申请失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"运行certbot时发生异常: {e}")
            return False
    
    def _get_auth_hook_script(self) -> str:
        """
        获取认证钩子脚本路径
        """
        # 这里应该创建一个临时脚本来处理DNS挑战
        # 为简化，我们使用内置的DNS挑战处理
        return "/tmp/certbot_auth_hook.sh"
    
    def _get_cleanup_hook_script(self) -> str:
        """
        获取清理钩子脚本路径
        """
        return "/tmp/certbot_cleanup_hook.sh"
    
    def copy_certs_for_nginx(self, domain: str) -> bool:
        """
        复制证书文件到nginx可用的位置
        
        Args:
            domain: 主域名
            
        Returns:
            是否复制成功
        """
        try:
            # Let's Encrypt证书路径
            le_cert_dir = Path(f"/etc/letsencrypt/live/{domain}")
            
            if not le_cert_dir.exists():
                self.logger.error(f"Let's Encrypt证书目录不存在: {le_cert_dir}")
                return False
            
            # 复制证书文件
            cert_files = {
                "fullchain.pem": self.cert_dir / f"{domain}.crt",
                "privkey.pem": self.private_key_dir / f"{domain}.key",
                "chain.pem": self.cert_dir / f"{domain}-chain.crt"
            }
            
            for src_name, dst_path in cert_files.items():
                src_path = le_cert_dir / src_name
                if src_path.exists():
                    shutil.copy2(src_path, dst_path)
                    # 设置适当的权限
                    if "key" in str(dst_path):
                        dst_path.chmod(0o600)
                    else:
                        dst_path.chmod(0o644)
                    self.logger.info(f"复制证书文件: {src_path} -> {dst_path}")
                else:
                    self.logger.warning(f"源证书文件不存在: {src_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"复制证书文件时发生异常: {e}")
            return False
    
    def reload_nginx(self) -> bool:
        """
        重新加载nginx配置
        
        Returns:
            是否重新加载成功
        """
        try:
            # 测试nginx配置
            result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"nginx配置测试失败: {result.stderr}")
                return False
            
            # 重新加载nginx
            result = subprocess.run(["nginx", "-s", "reload"], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("nginx重新加载成功")
                return True
            else:
                self.logger.error(f"nginx重新加载失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"重新加载nginx时发生异常: {e}")
            return False
    
    async def update_certificates(self) -> bool:
        """
        更新所有域名的证书
        
        Returns:
            是否全部更新成功
        """
        success_count = 0
        
        # 按主域名分组
        domain_groups = self._group_domains_by_main_domain()
        
        for main_domain, domain_list in domain_groups.items():
            self.logger.info(f"处理域名组: {main_domain} -> {domain_list}")
            
            # 检查是否需要续期
            needs_update = any(self.needs_renewal(domain) for domain in domain_list)
            
            if not needs_update:
                self.logger.info(f"域名组 {main_domain} 的证书都不需要更新")
                success_count += 1
                continue
            
            # 申请证书（使用简化的方式，实际应该集成完整的ACME客户端）
            if await self._request_certificate_for_domains(domain_list):
                # 复制证书文件
                if self.copy_certs_for_nginx(main_domain):
                    success_count += 1
                    self.logger.info(f"域名组 {main_domain} 证书更新成功")
                else:
                    self.logger.error(f"域名组 {main_domain} 证书文件复制失败")
            else:
                self.logger.error(f"域名组 {main_domain} 证书申请失败")
        
        # 如果有证书更新成功，重新加载nginx
        if success_count > 0:
            self.reload_nginx()
        
        total_groups = len(domain_groups)
        self.logger.info(f"证书更新完成: {success_count}/{total_groups} 个域名组成功")
        
        return success_count == total_groups
    
    def _group_domains_by_main_domain(self) -> Dict[str, List[str]]:
        """
        按主域名对域名进行分组
        
        Returns:
            域名分组字典
        """
        groups = {}
        for domain in self.domains:
            main_domain = self.extract_domain_from_fqdn(domain)
            if main_domain not in groups:
                groups[main_domain] = []
            groups[main_domain].append(domain)
        return groups
    
    async def _request_certificate_for_domains(self, domains: List[str]) -> bool:
        """
        为域名列表申请证书（简化版本）
        
        Args:
            domains: 域名列表
            
        Returns:
            是否申请成功
        """
        # 这里应该实现完整的ACME协议
        # 为了简化，我们假设使用certbot的DNS插件
        self.logger.info(f"开始为域名申请证书: {domains}")
        
        try:
            # 使用certbot DNS插件（需要预先配置）
            cmd = [
                "certbot", "certonly",
                "--dns-aliyun",
                "--dns-aliyun-credentials", "/etc/letsencrypt/aliyun.ini",
                "--server", self.acme_server,
                "--email", self.email,
                "--agree-tos",
                "--non-interactive"
            ]
            
            for domain in domains:
                cmd.extend(["-d", domain])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"证书申请成功: {domains}")
                return True
            else:
                self.logger.error(f"证书申请失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"申请证书时发生异常: {e}")
            return False
    
    async def run_once(self) -> bool:
        """
        执行一次证书更新检查和更新
        
        Returns:
            是否执行成功
        """
        try:
            self.logger.info("开始执行SSL证书更新检查")
            result = await self.update_certificates()
            self.logger.info(f"SSL证书更新检查完成，结果: {'成功' if result else '失败'}")
            return result
        except Exception as e:
            self.logger.error(f"执行SSL证书更新时发生异常: {e}")
            return False


# 命令行入口
@click.command()
@click.option('--domains', '-d', multiple=True, required=True, help='域名列表，可以指定多个')
@click.option('--email', '-e', required=True, help='Let\'s Encrypt账户邮箱')
@click.option('--cert-dir', default=CERT_DIR, help=f'证书存储目录，默认 {CERT_DIR}')
@click.option('--private-key-dir', default=PRIVATE_KEY_DIR, help=f'私钥存储目录，默认 {PRIVATE_KEY_DIR}')
@click.option('--staging', is_flag=True, help='使用Let\'s Encrypt测试环境')
@click.option('--log-file', default=LOG_FILE, help=f'日志文件路径，默认 {LOG_FILE}')
def main(domains, email, cert_dir, private_key_dir, staging, log_file):
    """SSL证书自动更新工具
    
    使用Let's Encrypt和阿里云DNS自动申请和更新SSL证书。
    
    示例:
    \b
    chattool.ssl-cert-updater -d example.com -d www.example.com -e admin@example.com
    chattool.ssl-cert-updater -d example.com -d api.example.com -d www.example.com -e admin@example.com --staging
    """
    logger = setup_logger('ssl_cert_updater', log_file)
    
    click.echo(f"启动SSL证书更新器...")
    click.echo(f"域名: {', '.join(domains)}")
    click.echo(f"邮箱: {email}")
    click.echo(f"证书目录: {cert_dir}")
    click.echo(f"私钥目录: {private_key_dir}")
    click.echo(f"环境: {'测试' if staging else '生产'}")
    click.echo("")
    
    updater = SSLCertUpdater(
        domains=list(domains),
        email=email,
        cert_dir=cert_dir,
        private_key_dir=private_key_dir,
        staging=staging,
        logger=logger
    )
    
    try:
        result = asyncio.run(updater.run_once())
        if result:
            click.echo("SSL证书更新成功")
        else:
            click.echo("SSL证书更新失败", err=True)
            raise click.Abort()
    except KeyboardInterrupt:
        click.echo("\n程序被用户中断")
    except Exception as e:
        click.echo(f"程序运行出错: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()