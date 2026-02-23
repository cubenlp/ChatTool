from typing import List, Optional, Any, Union
import os
try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = Any
from chattool.tools import create_dns_client, DynamicIPUpdater, SSLCertUpdater
from chattool.utils import setup_logger

logger = setup_logger("mcp_dns", log_level="INFO")

def _get_provider(provider: Optional[str] = None) -> str:
    """Helper to determine DNS provider"""
    if provider:
        return provider
    # Fallback to environment variable or default
    return os.getenv("DNS_PROVIDER", "aliyun")

def list_domains(provider: Optional[str] = None) -> Union[List[dict], str]:
    """
    List all domains under the DNS account.
    
    Args:
        provider: DNS provider ('aliyun' or 'tencent'). If None, uses default.
    """
    try:
        p = _get_provider(provider)
        client = create_dns_client(p, logger=logger)
        return client.describe_domains()
    except ImportError as e:
        logger.error(f"Dependency missing: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error listing domains: {e}")
        return f"Error: {str(e)}"

def get_records(domain: str, rr: Optional[str] = None, provider: Optional[str] = None) -> Union[List[dict], str]:
    """
    Get DNS records for a domain.
    
    Args:
        domain: Domain name (e.g., example.com)
        rr: Optional host record (e.g., www). If provided, filters by RR.
        provider: DNS provider ('aliyun' or 'tencent').
    """
    try:
        p = _get_provider(provider)
        client = create_dns_client(p, logger=logger)
        if rr:
            return client.describe_subdomain_records(domain, rr)
        return client.describe_domain_records(domain)
    except ImportError as e:
        logger.error(f"Dependency missing: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error getting records: {e}")
        return f"Error: {str(e)}"

def add_record(
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
    try:
        p = _get_provider(provider)
        client = create_dns_client(p, logger=logger)
        return client.add_domain_record(domain, rr, type, value, ttl)
    except ImportError as e:
        logger.error(f"Dependency missing: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error adding record: {e}")
        return f"Error: {str(e)}"

def delete_record(
    domain: str, 
    rr: str, 
    type: Optional[str] = None, 
    provider: Optional[str] = None
) -> Union[bool, str]:
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
    try:
        p = _get_provider(provider)
        client = create_dns_client(p, logger=logger)
        return client.delete_subdomain_records(domain, rr, type_=type)
    except ImportError as e:
        logger.error(f"Dependency missing: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error deleting record: {e}")
        return f"Error: {str(e)}"

async def ddns_update(
    domain: str, 
    rr: str, 
    ip_type: str = 'public', 
    provider: Optional[str] = None
) -> Union[bool, str]:
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
    try:
        p = _get_provider(provider)
        updater = DynamicIPUpdater(
            domain_name=domain,
            rr=rr,
            dns_type=p,
            ip_type=ip_type,
            logger=logger
        )
        return await updater.run_once()
    except ImportError as e:
        logger.error(f"Dependency missing: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in DDNS update: {e}")
        return f"Error: {str(e)}"

async def cert_update(
    domains: List[str], 
    email: str, 
    provider: Optional[str] = None, 
    staging: bool = False,
    cert_dir: Optional[str] = None
) -> Union[bool, str]:
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
    try:
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
    except ImportError as e:
        logger.error(f"Dependency missing: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in cert update: {e}")
        return f"Error: {str(e)}"

def register(mcp: FastMCP):
    """Register DNS tools with the MCP server."""
    mcp.tool(name="dns_list_domains", tags=["dns", "read"])(list_domains)
    mcp.tool(name="dns_get_records", tags=["dns", "read"])(get_records)
    mcp.tool(name="dns_add_record", tags=["dns", "write"])(add_record)
    mcp.tool(name="dns_delete_record", tags=["dns", "write"])(delete_record)
    mcp.tool(name="dns_ddns_update", tags=["dns", "write"])(ddns_update)
    mcp.tool(name="dns_cert_update", tags=["cert", "write"])(cert_update)
