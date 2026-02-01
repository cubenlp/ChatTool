#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal ACMEv2 client for DNS-01 challenge.
Based on acme-tiny by Daniel Roesler (MIT License).
Modernized to use requests and cryptography.
"""

import json
import base64
import hashlib
import time
import logging
from typing import List, Callable, Optional
import requests
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)

class AcmeError(Exception):
    pass

def get_crt(account_key: str, csr: str, 
            dns_update_callback: Callable[[str, str], None],
            dns_cleanup_callback: Callable[[str], None],
            directory_url: str = "https://acme-v02.api.letsencrypt.org/directory",
            contact: Optional[List[str]] = None) -> str:
    """
    Get certificate using ACMEv2 DNS-01 challenge.
    
    Args:
        account_key: PEM encoded account private key
        csr: PEM encoded certificate signing request
        dns_update_callback: Callback(domain, token) to set DNS TXT record
        dns_cleanup_callback: Callback(domain) to remove DNS TXT record
        directory_url: ACME directory URL
        contact: List of contact emails (e.g. ["mailto:admin@example.com"])
        
    Returns:
        PEM encoded signed certificate
    """
    
    # Helper function for base64url encoding
    def _b64(b):
        return base64.urlsafe_b64encode(b).decode('utf8').replace("=", "")

    # Parse account key
    try:
        private_key = serialization.load_pem_private_key(
            account_key.encode('utf8'), password=None
        )
    except Exception as e:
        raise AcmeError(f"Error loading account key: {e}")

    # Helper to sign messages
    def _sign_request(url, payload, nonce):
        payload64 = "" if payload is None else _b64(json.dumps(payload).encode('utf8'))
        
        # JWS Header
        # Note: Let's Encrypt ACME v2 requires "kid" for all requests except newAccount.
        # For newAccount, we use "jwk".
        
        header = {
            "url": url,
            "alg": "RS256",
            "nonce": nonce
        }
        
        if url == new_account_url:
            header["jwk"] = {
                "e": _b64(private_key.public_key().public_numbers().e.to_bytes(3, 'big')),
                "kty": "RSA",
                "n": _b64(private_key.public_key().public_numbers().n.to_bytes((private_key.key_size + 7) // 8, 'big'))
            }
        else:
            header["kid"] = account_url

        protected64 = _b64(json.dumps(header).encode('utf8'))
        
        signature = private_key.sign(
            f"{protected64}.{payload64}".encode('utf8'),
            padding=padding.PKCS1v15(),
            algorithm=hashes.SHA256()
        )
        
        return {
            "protected": protected64,
            "payload": payload64,
            "signature": _b64(signature)
        }

    # Helper to make signed requests
    def _send_signed_request(url, payload):
        nonlocal log_nonce
        resp = requests.head(new_nonce_url)
        new_nonce = resp.headers['Replay-Nonce']
        
        data = _sign_request(url, payload, new_nonce)
        try:
            resp = requests.post(url, json=data, headers={"Content-Type": "application/jose+json"})
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            if resp.content:
                logger.error(f"ACME Error Response: {resp.content.decode('utf8')}")
            raise AcmeError(f"ACME Request Failed: {e}")

    # 1. Get Directory
    logger.info("Getting ACME directory...")
    resp = requests.get(directory_url)
    directory = resp.json()
    new_nonce_url = directory['newNonce']
    new_account_url = directory['newAccount']
    new_order_url = directory['newOrder']
    
    # 2. Register Account
    logger.info("Registering account...")
    log_nonce = None
    payload = {"termsOfServiceAgreed": True}
    if contact:
        payload["contact"] = contact
        
    resp = _send_signed_request(new_account_url, payload)
    account_url = resp.headers['Location']
    logger.info(f"Account registered: {account_url}")

    # 3. Parse CSR to get domains
    csr_obj = x509.load_pem_x509_csr(csr.encode('utf8'))
    domains = [
        attr.value for attr in csr_obj.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
    ]
    try:
        san_ext = csr_obj.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        domains.extend(name.value for name in san_ext.value)
    except x509.ExtensionNotFound:
        pass
    
    domains = list(set(domains)) # Deduplicate
    logger.info(f"Domains to certify: {domains}")

    # 4. Create New Order
    logger.info("Creating new order...")
    payload = {"identifiers": [{"type": "dns", "value": d} for d in domains]}
    resp = _send_signed_request(new_order_url, payload)
    order = resp.json()
    order_url = resp.headers['Location']
    authorizations = order['authorizations']
    finalize_url = order['finalize']

    # 5. Handle Authorizations
    for auth_url in authorizations:
        resp = _send_signed_request(auth_url, None)
        auth = resp.json()
        domain = auth['identifier']['value']
        
        if auth['status'] == 'valid':
            logger.info(f"Domain {domain} is already verified.")
            continue
            
        logger.info(f"Verifying domain: {domain}")
        
        # Find DNS-01 challenge
        challenge = next((c for c in auth['challenges'] if c['type'] == 'dns-01'), None)
        if not challenge:
            raise AcmeError(f"No DNS-01 challenge found for {domain}")
            
        token = challenge['token']
        # Compute key authorization
        thumbprint = _b64(
            hashlib.sha256(
                json.dumps(
                    {
                        "e": _b64(private_key.public_key().public_numbers().e.to_bytes(3, 'big')),
                        "kty": "RSA",
                        "n": _b64(private_key.public_key().public_numbers().n.to_bytes((private_key.key_size + 7) // 8, 'big'))
                    }, 
                    sort_keys=True, separators=(',', ':')
                ).encode('utf8')
            ).digest()
        )
        key_authorization = f"{token}.{thumbprint}"
        txt_record_value = _b64(hashlib.sha256(key_authorization.encode('utf8')).digest())
        
        # Call DNS update callback
        logger.info(f"Setting DNS TXT record for {domain}...")
        dns_update_callback(domain, txt_record_value)
        
        # Wait for propagation (can be optimized by checking locally)
        logger.info("Waiting 30s for DNS propagation...")
        # Since we use Tencent DNS API, it might propagate faster or slower. 
        # But for test, maybe we need longer time or retry logic?
        # The error "DNS problem: NXDOMAIN looking up TXT" suggests it didn't propagate or wasn't added correctly.
        time.sleep(60) 
        
        # Verify Challenge
        logger.info(f"Submitting challenge for {domain}...")
        _send_signed_request(challenge['url'], {"keyAuthorization": key_authorization})
        
        # Poll for status
        while True:
            resp = _send_signed_request(auth_url, None)
            status = resp.json()['status']
            if status == 'valid':
                logger.info(f"Domain {domain} verified!")
                break
            if status == 'invalid':
                raise AcmeError(f"Domain {domain} verification failed: {resp.json()}")
            time.sleep(2)
            
        # Cleanup
        logger.info(f"Cleaning up DNS record for {domain}...")
        dns_cleanup_callback(domain)

    # 6. Finalize Order
    logger.info("Finalizing order...")
    # CSR must be base64url encoded without headers
    csr_der = csr_obj.public_bytes(serialization.Encoding.DER)
    _send_signed_request(finalize_url, {"csr": _b64(csr_der)})

    # 7. Get Certificate
    while True:
        resp = _send_signed_request(order_url, None)
        order = resp.json()
        if order['status'] == 'valid':
            break
        if order['status'] == 'invalid':
            raise AcmeError(f"Order failed: {order}")
        # Add 'ready' state which means we should poll finalize
        # But 'processing' means we wait for order to become valid.
        time.sleep(2)
        
    cert_url = order['certificate']
    resp = _send_signed_request(cert_url, None)
    
    # Return certificate chain
    return resp.text

