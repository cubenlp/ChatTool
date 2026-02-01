from typing import List, Optional
import os
from fastmcp import FastMCP
from chattool.tools.dns import create_dns_client, DynamicIPUpdater, SSLCertUpdater
from chattool.utils import setup_logger

# Initialize FastMCP server
mcp = FastMCP("ChatTool DNS Manager")

# Logger for MCP tools
logger = setup_logger("mcp_server", log_level="INFO")

def _get_provider(provider: Optional[str] = None) -> str:
    """Helper to determine DNS provider"""
    if provider:
        return provider
    # Fallback to environment variable or default
    return os.getenv("DNS_PROVIDER", "aliyun")

@mcp.tool(tags=["dns", "read"])
def dns_list_domains(provider: Optional[str] = None) -> List[dict]:
    """
    List all domains under the DNS account.
    
    Args:
        provider: DNS provider ('aliyun' or 'tencent'). If None, uses default.
    """
    p = _get_provider(provider)
    client = create_dns_client(p, logger=logger)
    return client.describe_domains()

@mcp.tool(tags=["dns", "read"])
def dns_get_records(domain: str, rr: Optional[str] = None, provider: Optional[str] = None) -> List[dict]:
    """
    Get DNS records for a domain.
    
    Args:
        domain: Domain name (e.g., example.com)
        rr: Optional host record (e.g., www). If provided, filters by RR.
        provider: DNS provider ('aliyun' or 'tencent').
    """
    p = _get_provider(provider)
    client = create_dns_client(p, logger=logger)
    if rr:
        return client.describe_subdomain_records(domain, rr)
    return client.describe_domain_records(domain)

@mcp.tool(tags=["dns", "write"])
def dns_add_record(
    domain: str, 
    rr: str, 
    type: str, 
    value: str, 
    ttl: int = 600, 
    provider: Optional[str] = None
) -> str:
    """
    Add a new DNS record.
    
    Args:
        domain: Domain name
        rr: Host record (e.g., www)
        type: Record type (A, AAAA, CNAME, TXT, etc.)
        value: Record value
        ttl: Time to live
        provider: DNS provider
    
    Returns:
        The Record ID of the created record.
    """
    p = _get_provider(provider)
    client = create_dns_client(p, logger=logger)
    return client.add_domain_record(domain, rr, type, value, ttl)

@mcp.tool(tags=["dns", "write"])
def dns_delete_record(
    domain: str, 
    rr: str, 
    type: Optional[str] = None, 
    provider: Optional[str] = None
) -> bool:
    """
    Delete DNS records.
    
    Args:
        domain: Domain name
        rr: Host record to delete
        type: Optional record type to filter deletion
        provider: DNS provider
        
    Returns:
        True if deletion logic executed successfully.
    """
    p = _get_provider(provider)
    client = create_dns_client(p, logger=logger)
    return client.delete_subdomain_records(domain, rr, type_=type)

@mcp.tool(tags=["dns", "write"])
async def dns_ddns_update(
    domain: str, 
    rr: str, 
    ip_type: str = 'public', 
    provider: Optional[str] = None
) -> bool:
    """
    Perform a DDNS update (update DNS record with current IP).
    
    Args:
        domain: Domain name
        rr: Host record
        ip_type: 'public' or 'local'
        provider: DNS provider
        
    Returns:
        True if update succeeded or no change needed.
    """
    p = _get_provider(provider)
    updater = DynamicIPUpdater(
        domain_name=domain,
        rr=rr,
        dns_type=p,
        ip_type=ip_type,
        logger=logger
    )
    return await updater.run_once()

@mcp.tool(tags=["cert", "write"])
async def dns_cert_update(
    domains: List[str], 
    email: str, 
    provider: Optional[str] = None, 
    staging: bool = False,
    cert_dir: Optional[str] = None
) -> bool:
    """
    Request or renew SSL certificates using Let's Encrypt (DNS-01 challenge).
    
    Args:
        domains: List of domains to include in the certificate.
        email: Email for Let's Encrypt registration.
        provider: DNS provider used for validation.
        staging: Use Let's Encrypt staging environment (for testing).
        cert_dir: Directory to save certificates (optional).
        
    Returns:
        True if certificate was successfully obtained or renewed.
    """
    p = _get_provider(provider)
    
    # Handle optional cert_dir: pass it only if not None, otherwise let class use default
    kwargs = {}
    if cert_dir:
        kwargs['cert_dir'] = cert_dir
        
    updater = SSLCertUpdater(
        domains=domains,
        email=email,
        dns_type=p,
        staging=staging,
        logger=logger,
        **kwargs
    )
    return await updater.run_once()

# --- Configuration & Visibility ---

def _configure_visibility():
    """Configure tool visibility based on environment variables."""
    enable_tags_str = os.getenv("CHATTOOL_MCP_ENABLE_TAGS")
    disable_tags_str = os.getenv("CHATTOOL_MCP_DISABLE_TAGS")

    if enable_tags_str:
        tags = {t.strip() for t in enable_tags_str.split(",") if t.strip()}
        if tags:
            logger.info(f"Enabling only tools with tags: {tags}")
            mcp.include_tags = tags
    
    if disable_tags_str:
        tags = {t.strip() for t in disable_tags_str.split(",") if t.strip()}
        if tags:
            logger.info(f"Disabling tools with tags: {tags}")
            mcp.exclude_tags = tags

# Apply configuration
_configure_visibility()
