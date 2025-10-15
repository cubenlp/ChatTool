#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL证书自动更新工具 - 基于Let's Encrypt和腾讯云DNSPod

使用Let's Encrypt的DNS-01挑战验证方式自动申请和更新SSL证书。
支持多域名，自动管理DNS TXT记录，生成nginx可用的证书文件。
"""

import os
import time
import click
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import subprocess
import tempfile
import shutil
from batch_executor import setup_logger
from .client import TencentDNSClient

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
                 logger=None):
        """
        初始化SSL证书更新器
        
        Args:
            domains: 域名列表
            email: Let's Encrypt账户邮箱
            cert_dir: 证书存储目录
            private_key_dir: 私钥存储目录
            staging: 是否使用Let's Encrypt测试环境
            logger: 日志记录器
        """
        self.domains = domains
        self.email = email
        self.cert_dir = Path(cert_dir)
        self.private_key_dir = Path(private_key_dir)
        self.staging = staging
        self.logger = logger or setup_logger(__name__)
        
        # 确保目录存在
        self.cert_dir.mkdir(parents=True, exist_ok=True)
        self.private_key_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化DNS客户端
        try:
            self.dns_client = TencentDNSClient(logger=self.logger)
            self.logger.info("腾讯云DNS客户端初始化成功")
        except Exception as e:
            self.logger.error(f"腾讯云DNS客户端初始化失败: {e}")
            raise
        
        # 设置acme.sh相关路径
        self.acme_sh_dir = Path.home() / ".acme.sh"
        self.acme_sh_bin = self.acme_sh_dir / "acme.sh"
        
        # Let's Encrypt服务器URL
        if staging:
            self.server_url = "https://acme-staging-v02.api.letsencrypt.org/directory"
            self.logger.info("使用Let's Encrypt测试环境")
        else:
            self.server_url = "https://acme-v02.api.letsencrypt.org/directory"
            self.logger.info("使用Let's Encrypt生产环境")
    
    def check_acme_sh_installed(self) -> bool:
        """检查acme.sh是否已安装"""
        return self.acme_sh_bin.exists()
    
    def install_acme_sh(self) -> bool:
        """安装acme.sh"""
        try:
            self.logger.info("开始安装acme.sh...")
            
            # 下载并安装acme.sh
            install_cmd = [
                "curl", "https://get.acme.sh", "|", "sh", "-s", 
                "email=" + self.email
            ]
            
            # 使用shell执行安装命令
            result = subprocess.run(
                " ".join(install_cmd),
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.logger.info("acme.sh安装成功")
                return True
            else:
                self.logger.error(f"acme.sh安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"安装acme.sh时发生异常: {e}")
            return False
    
    def extract_domain_parts(self, domain: str) -> Tuple[str, str]:
        """提取域名的主域名和子域名部分"""
        parts = domain.split('.')
        if len(parts) < 2:
            raise ValueError(f"无效的域名格式: {domain}")
        
        # 假设最后两部分是主域名
        if len(parts) == 2:
            return domain, "@"
        else:
            main_domain = '.'.join(parts[-2:])
            subdomain = '.'.join(parts[:-2])
            return main_domain, subdomain
    
    def add_txt_record(self, domain: str, value: str) -> bool:
        """添加DNS TXT记录用于ACME挑战"""
        try:
            challenge_domain = f"_acme-challenge.{domain}"
            main_domain, subdomain = self.extract_domain_parts(challenge_domain)
            
            self.logger.info(f"添加DNS TXT记录: {challenge_domain} -> {value}")
            
            record_id = self.dns_client.add_domain_record(
                domain_name=main_domain,
                rr=subdomain,
                type_="TXT",
                value=value,
                ttl=ACME_CHALLENGE_TTL
            )
            
            if record_id:
                self.logger.info(f"DNS TXT记录添加成功，记录ID: {record_id}")
                return True
            else:
                self.logger.error("DNS TXT记录添加失败")
                return False
                
        except Exception as e:
            self.logger.error(f"添加DNS TXT记录时发生异常: {e}")
            return False
    
    def remove_txt_record(self, domain: str) -> bool:
        """删除DNS TXT记录"""
        try:
            challenge_domain = f"_acme-challenge.{domain}"
            main_domain, subdomain = self.extract_domain_parts(challenge_domain)
            
            self.logger.info(f"删除DNS TXT记录: {challenge_domain}")
            
            # 查找并删除所有匹配的TXT记录
            records = self.dns_client.describe_domain_records(
                domain_name=main_domain,
                subdomain=subdomain,
                record_type="TXT"
            )
            
            success = True
            for record in records:
                if self.dns_client.delete_domain_record(record['RecordId'], main_domain):
                    self.logger.info(f"删除DNS TXT记录成功: {record['RecordId']}")
                else:
                    self.logger.error(f"删除DNS TXT记录失败: {record['RecordId']}")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"删除DNS TXT记录时发生异常: {e}")
            return False
    
    def wait_for_dns_propagation(self, domain: str, value: str) -> bool:
        """等待DNS记录传播"""
        challenge_domain = f"_acme-challenge.{domain}"
        self.logger.info(f"等待DNS记录传播: {challenge_domain}")
        
        # 等待指定时间
        for i in range(CHALLENGE_WAIT_TIME):
            if i % 10 == 0:
                self.logger.info(f"等待DNS传播... ({i}/{CHALLENGE_WAIT_TIME}秒)")
            time.sleep(1)
        
        # 验证DNS记录
        try:
            import dns.resolver
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(challenge_domain, 'TXT')
            
            for answer in answers:
                if value in str(answer):
                    self.logger.info("DNS记录传播验证成功")
                    return True
            
            self.logger.warning("DNS记录传播验证失败，但继续执行")
            return True  # 继续执行，让ACME服务器验证
            
        except Exception as e:
            self.logger.warning(f"DNS记录传播验证失败: {e}，但继续执行")
            return True  # 继续执行，让ACME服务器验证
    
    def issue_certificate(self) -> bool:
        """申请证书"""
        try:
            if not self.check_acme_sh_installed():
                if not self.install_acme_sh():
                    return False
            
            # 构建域名参数
            domain_args = []
            for domain in self.domains:
                domain_args.extend(["-d", domain])
            
            # 主域名
            primary_domain = self.domains[0]
            
            # 构建acme.sh命令
            cmd = [
                str(self.acme_sh_bin),
                "--issue",
                "--dns", "dns_manual",
                "--server", self.server_url,
                "--email", self.email,
                "--key-file", str(self.private_key_dir / f"{primary_domain}.key"),
                "--cert-file", str(self.cert_dir / f"{primary_domain}.crt"),
                "--ca-file", str(self.cert_dir / f"{primary_domain}.ca.crt"),
                "--fullchain-file", str(self.cert_dir / f"{primary_domain}.fullchain.crt"),
                "--force"
            ] + domain_args
            
            self.logger.info(f"开始申请证书: {', '.join(self.domains)}")
            
            # 执行acme.sh命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                self.logger.info("证书申请成功")
                return True
            else:
                self.logger.error(f"证书申请失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"申请证书时发生异常: {e}")
            return False
    
    def renew_certificate(self) -> bool:
        """续期证书"""
        try:
            primary_domain = self.domains[0]
            
            cmd = [
                str(self.acme_sh_bin),
                "--renew",
                "-d", primary_domain,
                "--force"
            ]
            
            self.logger.info(f"开始续期证书: {primary_domain}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                self.logger.info("证书续期成功")
                return True
            else:
                self.logger.error(f"证书续期失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"续期证书时发生异常: {e}")
            return False
    
    def check_certificate_expiry(self) -> Optional[datetime]:
        """检查证书过期时间"""
        try:
            primary_domain = self.domains[0]
            cert_file = self.cert_dir / f"{primary_domain}.crt"
            
            if not cert_file.exists():
                self.logger.info("证书文件不存在")
                return None
            
            # 使用openssl检查证书过期时间
            cmd = ["openssl", "x509", "-in", str(cert_file), "-noout", "-enddate"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 解析过期时间
                date_str = result.stdout.strip().replace("notAfter=", "")
                expiry_date = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                
                self.logger.info(f"证书过期时间: {expiry_date}")
                return expiry_date
            else:
                self.logger.error(f"检查证书过期时间失败: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"检查证书过期时间时发生异常: {e}")
            return None
    
    def needs_renewal(self) -> bool:
        """检查是否需要续期"""
        expiry_date = self.check_certificate_expiry()
        if not expiry_date:
            return True  # 没有证书或检查失败，需要申请
        
        days_until_expiry = (expiry_date - datetime.now()).days
        self.logger.info(f"证书还有 {days_until_expiry} 天过期")
        
        return days_until_expiry <= CERT_RENEWAL_DAYS
    
    def update_certificates(self) -> bool:
        """更新证书"""
        try:
            if not self.needs_renewal():
                self.logger.info("证书不需要更新")
                return True
            
            # 检查是否已有证书
            primary_domain = self.domains[0]
            cert_file = self.cert_dir / f"{primary_domain}.crt"
            
            if cert_file.exists():
                # 续期现有证书
                success = self.renew_certificate()
            else:
                # 申请新证书
                success = self.issue_certificate()
            
            if success:
                self.logger.info("证书更新成功")
                # TODO: 可以在这里添加重启web服务器的逻辑
                return True
            else:
                self.logger.error("证书更新失败")
                return False
                
        except Exception as e:
            self.logger.error(f"更新证书时发生异常: {e}")
            return False


# CLI 接口
@click.group()
def cli():
    """腾讯云DNSPod SSL证书自动更新工具"""
    pass

@cli.command()
@click.option('--domains', '-d', required=True, multiple=True, help='域名列表')
@click.option('--email', '-e', required=True, help='Let\'s Encrypt邮箱')
@click.option('--cert-dir', default=CERT_DIR, help=f'证书存储目录 (默认: {CERT_DIR})')
@click.option('--private-key-dir', default=PRIVATE_KEY_DIR, help=f'私钥存储目录 (默认: {PRIVATE_KEY_DIR})')
@click.option('--staging', is_flag=True, help='使用Let\'s Encrypt测试环境')
@click.option('--log-file', help='日志文件路径')
@click.option('--log-level', default='INFO', help='日志级别 (默认: INFO)')
def issue(domains, email, cert_dir, private_key_dir, staging, log_file, log_level):
    """申请新的SSL证书"""
    
    # 设置日志
    logger = setup_logger(
        name="tencent_ssl_issue",
        log_file=log_file or LOG_FILE,
        log_level=log_level,
        format_type="detailed"
    )
    
    # 创建证书更新器
    updater = SSLCertUpdater(
        domains=list(domains),
        email=email,
        cert_dir=cert_dir,
        private_key_dir=private_key_dir,
        staging=staging,
        logger=logger
    )
    
    # 申请证书
    try:
        if updater.issue_certificate():
            logger.info("证书申请成功")
        else:
            logger.error("证书申请失败")
            exit(1)
    except Exception as e:
        logger.error(f"证书申请失败: {e}")
        exit(1)

@cli.command()
@click.option('--domains', '-d', required=True, multiple=True, help='域名列表')
@click.option('--email', '-e', required=True, help='Let\'s Encrypt邮箱')
@click.option('--cert-dir', default=CERT_DIR, help=f'证书存储目录 (默认: {CERT_DIR})')
@click.option('--private-key-dir', default=PRIVATE_KEY_DIR, help=f'私钥存储目录 (默认: {PRIVATE_KEY_DIR})')
@click.option('--staging', is_flag=True, help='使用Let\'s Encrypt测试环境')
@click.option('--log-file', help='日志文件路径')
@click.option('--log-level', default='INFO', help='日志级别 (默认: INFO)')
def renew(domains, email, cert_dir, private_key_dir, staging, log_file, log_level):
    """续期现有SSL证书"""
    
    # 设置日志
    logger = setup_logger(
        name="tencent_ssl_renew",
        log_file=log_file or LOG_FILE,
        log_level=log_level,
        format_type="detailed"
    )
    
    # 创建证书更新器
    updater = SSLCertUpdater(
        domains=list(domains),
        email=email,
        cert_dir=cert_dir,
        private_key_dir=private_key_dir,
        staging=staging,
        logger=logger
    )
    
    # 续期证书
    try:
        if updater.renew_certificate():
            logger.info("证书续期成功")
        else:
            logger.error("证书续期失败")
            exit(1)
    except Exception as e:
        logger.error(f"证书续期失败: {e}")
        exit(1)

@cli.command()
@click.option('--domains', '-d', required=True, multiple=True, help='域名列表')
@click.option('--email', '-e', required=True, help='Let\'s Encrypt邮箱')
@click.option('--cert-dir', default=CERT_DIR, help=f'证书存储目录 (默认: {CERT_DIR})')
@click.option('--private-key-dir', default=PRIVATE_KEY_DIR, help=f'私钥存储目录 (默认: {PRIVATE_KEY_DIR})')
@click.option('--staging', is_flag=True, help='使用Let\'s Encrypt测试环境')
@click.option('--log-file', help='日志文件路径')
@click.option('--log-level', default='INFO', help='日志级别 (默认: INFO)')
def auto_update(domains, email, cert_dir, private_key_dir, staging, log_file, log_level):
    """自动检查并更新SSL证书"""
    
    # 设置日志
    logger = setup_logger(
        name="tencent_ssl_auto",
        log_file=log_file or LOG_FILE,
        log_level=log_level,
        format_type="detailed"
    )
    
    # 创建证书更新器
    updater = SSLCertUpdater(
        domains=list(domains),
        email=email,
        cert_dir=cert_dir,
        private_key_dir=private_key_dir,
        staging=staging,
        logger=logger
    )
    
    # 自动更新证书
    try:
        if updater.update_certificates():
            logger.info("证书更新完成")
        else:
            logger.error("证书更新失败")
            exit(1)
    except Exception as e:
        logger.error(f"证书更新失败: {e}")
        exit(1)

@cli.command()
@click.option('--domains', '-d', required=True, multiple=True, help='域名列表')
@click.option('--email', '-e', required=True, help='Let\'s Encrypt邮箱')
@click.option('--cert-dir', default=CERT_DIR, help=f'证书存储目录 (默认: {CERT_DIR})')
@click.option('--private-key-dir', default=PRIVATE_KEY_DIR, help=f'私钥存储目录 (默认: {PRIVATE_KEY_DIR})')
@click.option('--staging', is_flag=True, help='使用Let\'s Encrypt测试环境')
def check(domains, email, cert_dir, private_key_dir, staging):
    """检查证书状态"""
    
    logger = setup_logger("tencent_ssl_check", log_level="INFO", format_type="simple")
    
    updater = SSLCertUpdater(
        domains=list(domains),
        email=email,
        cert_dir=cert_dir,
        private_key_dir=private_key_dir,
        staging=staging,
        logger=logger
    )
    
    # 检查证书状态
    expiry_date = updater.check_certificate_expiry()
    if expiry_date:
        days_until_expiry = (expiry_date - datetime.now()).days
        click.echo(f"证书过期时间: {expiry_date}")
        click.echo(f"距离过期还有: {days_until_expiry} 天")
        
        if updater.needs_renewal():
            click.echo("⚠️  证书需要更新")
        else:
            click.echo("✅ 证书状态正常")
    else:
        click.echo("❌ 证书不存在或检查失败")

if __name__ == '__main__':
    cli()
