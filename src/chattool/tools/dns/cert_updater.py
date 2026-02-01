#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL 证书自动更新工具 - 基于 Let's Encrypt 和阿里云 DNS

使用 Let's Encrypt 的 DNS-01 挑战验证方式自动申请和更新 SSL 证书。
支持多域名，自动管理 DNS TXT 记录，生成 nginx 可用的证书文件。
"""
import asyncio
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Union
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.x509.oid import NameOID

from chattool.utils import setup_logger

from .utils import create_dns_client, DNSClientType
from .acme_dns_tiny import get_crt

# 证书相关配置
ACME_CHALLENGE_TTL = 120                 # DNS挑战记录TTL
CHALLENGE_WAIT_TIME = 60                 # 等待DNS传播时间
CERT_RENEWAL_DAYS = 30                   # 证书续期提前天数

class SSLCertUpdater:
    """SSL证书自动更新器"""
    
    def __init__(self, 
                 domains: List[str],
                 email: str,
                 cert_dir: str = "certs",
                 staging: bool = False,
                 logger=None,
                 log_file: Optional[str] = None,
                 dns_type: Union[DNSClientType, str]='aliyun',
                 **dns_client_kwargs
        ):
        """
        初始化SSL证书更新器
        
        Args:
            domains: 域名列表
            email: Let's Encrypt账户邮箱
            cert_dir: 证书存储目录
            staging: 是否使用Let's Encrypt测试环境
            logger: 日志记录器
            log_file: 日志文件路径 (如果未提供 logger 且需要文件日志)
            dns_type: DNS客户端类型
            dns_client_kwargs: DNS客户端初始化参数
        """
        self.domains = domains
        self.email = email
        self.cert_dir = Path(cert_dir)
        self.staging = staging
        self.logger = logger or setup_logger(__name__, log_file=log_file)
        
        # 初始化DNS客户端
        self.dns_client = create_dns_client(dns_type, logger=self.logger, **dns_client_kwargs)
        
        # 创建目录
        self.cert_dir.mkdir(parents=True, exist_ok=True)
        
        # Let's Encrypt服务器URL
        self.acme_server = (
            "https://acme-staging-v02.api.letsencrypt.org/directory" if staging
            else "https://acme-v02.api.letsencrypt.org/directory"
        )
        
        self.logger.info(f"SSL证书更新器初始化完成")
        self.logger.info(f"域名: {', '.join(self.domains)}")
        self.logger.info(f"邮箱: {self.email}")
        self.logger.info(f"证书目录: {self.cert_dir}")
        self.logger.info(f"环境: {'测试' if staging else '生产'}")
    
    def check_cert_expiry(self, domain: str) -> Optional[datetime]:
        """
        检查证书过期时间
        
        Args:
            domain: 域名
            
        Returns:
            证书过期时间，如果证书不存在返回None
        """
        # Handle wildcard replacement in path
        file_domain_name = domain.replace("*", "_")
        cert_file = self.cert_dir / file_domain_name / "fullchain.pem"
        
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
        # 简单处理：取最后两段作为主域名
        # 对于复杂域名（如 .com.cn），可能需要更复杂的逻辑
        # 这里暂时假设是最后两段
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return fqdn
    
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
                success_count += 1
                self.logger.info(f"域名组 {main_domain} 证书更新成功")
            else:
                self.logger.error(f"域名组 {main_domain} 证书申请失败")
        
        
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
    
    def _ensure_account_key(self) -> str:
        """Ensure account key exists and return it. Uses RSA 2048 for account key (ACME requirement/standard)."""
        key_path = self.cert_dir / "account.key"
        if not key_path.exists():
            self.logger.info("Generating new account key (RSA 2048)...")
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            key_path.write_bytes(pem)
            # Secure permissions
            key_path.chmod(0o600)
            
        return key_path.read_text()

    def _ensure_domain_key(self, domain: str) -> str:
        """Ensure domain key exists and return it. Uses ECDSA secp384r1 for domain key (Modern, shorter)."""
        key_path = self.cert_dir / f"{domain}.key"
        if not key_path.exists():
            self.logger.info(f"Generating new private key for {domain} (ECDSA secp384r1)...")
            # Use ECDSA secp384r1 (P-384)
            private_key = ec.generate_private_key(ec.SECP384R1())
            
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            key_path.write_bytes(pem)
            key_path.chmod(0o600)
            
        return key_path.read_text()

    def verify_certificate_key_match(self, cert_path: Path, key_path: Path) -> bool:
        """
        Verify that the certificate matches the private key.
        
        Args:
            cert_path: Path to the certificate file (PEM format)
            key_path: Path to the private key file (PEM format)
            
        Returns:
            True if they match, False otherwise
        """
        try:
            cert_pem = cert_path.read_bytes()
            key_pem = key_path.read_bytes()
            
            cert = x509.load_pem_x509_certificate(cert_pem)
            private_key = serialization.load_pem_private_key(key_pem, password=None)
            
            cert_public_key = cert.public_key()
            private_key_public_key = private_key.public_key()
            
            # For Elliptic Curve keys
            if isinstance(cert_public_key, ec.EllipticCurvePublicKey) and \
               isinstance(private_key_public_key, ec.EllipticCurvePublicKey):
                # Compare curve name and public numbers
                if cert_public_key.curve.name != private_key_public_key.curve.name:
                    return False
                return cert_public_key.public_numbers() == private_key_public_key.public_numbers()
            
            # For RSA keys (legacy)
            if isinstance(cert_public_key, rsa.RSAPublicKey) and \
               isinstance(private_key_public_key, rsa.RSAPublicKey):
                return cert_public_key.public_numbers() == private_key_public_key.public_numbers()
                
            # Mismatched key types
            return False
            
        except Exception as e:
            self.logger.error(f"Certificate/Key verification failed: {e}")
            return False
    
    def _generate_csr(self, main_domain: str, domains: List[str], domain_key_pem: str) -> str:
        """Generate CSR for the domain list"""
        
        private_key = serialization.load_pem_private_key(domain_key_pem.encode('utf8'), password=None)
        
        builder = x509.CertificateSigningRequestBuilder()
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, main_domain),
        ]))
        
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(d) for d in domains]),
            critical=False,
        )
        
        csr = builder.sign(private_key, hashes.SHA256())
        return csr.public_bytes(serialization.Encoding.PEM).decode('utf8')

    async def _request_certificate_for_domains(self, domains: List[str]) -> bool:
        """
        使用 ACME 协议申请证书
        
        Args:
            domains: 域名列表
            
        Returns:
            是否申请成功
            
        Logic:
        1. 确定主域名 (用于文件名和 CN): 取列表第一个域名。
        2. 生成 Account Key (如果不存在): 使用 RSA 2048。
        3. 生成 Domain Private Key (如果不存在): 使用 ECDSA secp384r1 (更安全且短)。
        4. 生成 CSR (Certificate Signing Request)。
        5. 调用 `acme_dns_tiny.get_crt` 获取证书:
            - 该函数是同步阻塞的，因此在 `run_in_executor` 中运行以避免阻塞 asyncio 循环。
            - 传递两个回调函数 `dns_update` 和 `dns_cleanup` 用于处理 DNS-01 挑战。
            - 回调函数内部调用 `self.dns_client` (同步方法) 添加/删除 TXT 记录。
        6. 保存证书文件:
            - `privkey.pem`: 私钥
            - `fullchain.pem`: 完整证书链 (从 ACME 获取)
            - `cert.pem`: 叶子证书 (从 fullchain 分离)
            - `chain.pem`: 中间证书 (从 fullchain 分离)
        7. 验证证书与私钥是否匹配 (`verify_certificate_key_match`)。
        """
        self.logger.info(f"Starting ACME process for: {domains}")
        
        main_domain = domains[0]
        # Filename logic: replace wildcard "*" with "_"
        file_domain_name = main_domain.replace("*", "_")
        
        try:
            account_key = self._ensure_account_key()
            domain_key = self._ensure_domain_key(file_domain_name)
            csr = self._generate_csr(main_domain, domains, domain_key)
            
            # Callbacks for DNS challenge (executed in thread executor context)
            def dns_update(domain, token):
                self.logger.info(f"Callback: Updating DNS for {domain}")
                
                main_d = self.extract_domain_from_fqdn(domain)
                if domain == main_d:
                    rr = "_acme-challenge"
                else:
                    sub = domain[:-len(main_d)-1]
                    rr = f"_acme-challenge.{sub}"
                
                # Sync call to DNS client
                self.dns_client.add_domain_record(
                    domain_name=main_d, rr=rr, type_="TXT", value=token, ttl=600
                )
            
            def dns_cleanup(domain):
                self.logger.info(f"Callback: Cleaning DNS for {domain}")
                main_d = self.extract_domain_from_fqdn(domain)
                
                if domain == main_d:
                    rr = "_acme-challenge"
                else:
                    sub = domain[:-len(main_d)-1]
                    rr = f"_acme-challenge.{sub}"
                    
                self.dns_client.delete_record_value(main_d, rr, "TXT")

            # Run get_crt in executor to avoid blocking async loop
            loop = asyncio.get_running_loop()
            crt_pem = await loop.run_in_executor(
                None, 
                lambda: get_crt(
                    account_key, 
                    csr, 
                    dns_update, 
                    dns_cleanup,
                    directory_url=self.acme_server,
                    contact=[f"mailto:{self.email}"]
                )
            )
            
            # Save certificate and key in domain directory
            domain_dir = self.cert_dir / file_domain_name
            domain_dir.mkdir(parents=True, exist_ok=True)
            
            # Save Private Key
            key_path = domain_dir / "privkey.pem"
            key_path.write_text(domain_key)
            key_path.chmod(0o600)
            self.logger.info(f"Private Key saved to {key_path}")

            # Save Full Chain
            fullchain_path = domain_dir / "fullchain.pem"
            fullchain_path.write_text(crt_pem)
            self.logger.info(f"Full Chain saved to {fullchain_path}")
            
            # Split into cert and chain
            try:
                parts = crt_pem.strip().split("-----END CERTIFICATE-----")
                if len(parts) > 1:
                    leaf_cert = parts[0] + "-----END CERTIFICATE-----\n"
                    chain_cert = "-----END CERTIFICATE-----".join(parts[1:]).strip()
                    if chain_cert:
                            chain_cert += "-----END CERTIFICATE-----\n"
                    
                    # Save leaf cert
                    cert_path = domain_dir / "cert.pem"
                    cert_path.write_text(leaf_cert)
                    self.logger.info(f"Cert saved to {cert_path}")
                    
                    # Save chain
                    if chain_cert:
                        chain_path = domain_dir / "chain.pem"
                        chain_path.write_text(chain_cert)
                        self.logger.info(f"Chain saved to {chain_path}")
            except Exception as e:
                self.logger.warning(f"Failed to split certificate chain: {e}")

            # Verify Certificate Match
            if self.verify_certificate_key_match(domain_dir / "cert.pem", key_path):
                self.logger.info("Certificate verification successful: Matches private key")
            else:
                self.logger.error("Certificate verification FAILED: Does not match private key!")
                return False

            return True

        except Exception as e:
            self.logger.error(f"ACME Tiny process failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
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
