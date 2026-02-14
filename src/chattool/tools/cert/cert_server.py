import asyncio
import uuid
import hashlib
import json
import shutil
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
from chattool.tools.dns.cert_updater import SSLCertUpdater
from chattool.utils import setup_logger

# 全局配置
config = {
    "cert_dir": "certs", # 基础存储目录
    "provider": "aliyun",
    "secret_id": None,
    "secret_key": None
}

app = FastAPI(
    title="SSL 证书服务",
    description="提供 SSL 证书的异步申请与安全下载服务（支持多租户隔离）",
    version="1.0.0"
)

# --- 工具函数 ---

def get_token_hash(token: str) -> str:
    """计算 Token 哈希值，用于目录隔离"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()[:16]

def get_user_cert_dir(token_hash: str) -> Path:
    """获取用户专属证书目录"""
    return Path(config["cert_dir"]) / token_hash

def get_metadata_file(token_hash: str) -> Path:
    """获取用户元数据文件路径"""
    return get_user_cert_dir(token_hash) / "metadata.json"

def load_metadata(token_hash: str) -> List[Dict]:
    """加载用户元数据"""
    meta_file = get_metadata_file(token_hash)
    if not meta_file.exists():
        return []
    try:
        return json.loads(meta_file.read_text(encoding='utf-8'))
    except:
        return []

def save_metadata(token_hash: str, data: List[Dict]):
    """保存用户元数据"""
    meta_file = get_metadata_file(token_hash)
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    meta_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

# --- 模型定义 ---

class ApplyRequest(BaseModel):
    domains: List[str] = Field(..., description="域名列表，第一个为主域名")
    email: str = Field(..., description="Let's Encrypt 账户邮箱")
    provider: Optional[str] = Field(None, description="DNS 提供商 (aliyun/tencent)")
    secret_id: Optional[str] = Field(None, description="云厂商 Secret ID")
    secret_key: Optional[str] = Field(None, description="云厂商 Secret Key")

class CertRecord(BaseModel):
    domain: str
    domains: List[str]
    created_at: str
    expires_at: Optional[str]
    days_remaining: Optional[int]
    cert_path: str
    key_path: str

# --- 依赖项 ---

async def get_current_user_token(x_chattool_token: Optional[str] = Header(None)) -> str:
    """获取并校验当前用户 Token"""
    if not x_chattool_token:
        raise HTTPException(status_code=403, detail="Missing Token")
    return x_chattool_token

# --- 后台任务 ---

async def run_cert_update_task(token: str, req: ApplyRequest):
    """执行证书更新任务"""
    token_hash = get_token_hash(token)
    user_dir = get_user_cert_dir(token_hash)
    
    # 任务日志单独存放
    log_dir = user_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    task_id = str(uuid.uuid4())
    logger = setup_logger(f"cert_task_{task_id}", log_file=str(log_dir / f"{task_id}.log"))
    
    try:
        logger.info(f"Starting certificate task for {req.domains}")
        
        # 准备参数
        provider = req.provider or config["provider"]
        
        # 优先使用请求参数，其次使用全局配置
        dns_kwargs = {}
        secret_id = req.secret_id or config["secret_id"]
        secret_key = req.secret_key or config["secret_key"]
        
        if provider == "aliyun":
            if secret_id: dns_kwargs["access_key_id"] = secret_id
            if secret_key: dns_kwargs["access_key_secret"] = secret_key
        elif provider == "tencent":
            if secret_id: dns_kwargs["secret_id"] = secret_id
            if secret_key: dns_kwargs["secret_key"] = secret_key
            
        updater = SSLCertUpdater(
            domains=req.domains,
            email=req.email,
            cert_dir=str(user_dir), # 关键：使用用户隔离目录
            dns_type=provider,
            logger=logger,
            **dns_kwargs
        )
        
        success = await updater.run_once()
        
        if success:
            main_domain = req.domains[0]
            # Handle wildcard replacement in path
            file_domain_name = main_domain.replace("*", "_")
            
            # 解析证书有效期
            expiry_date = updater.check_cert_expiry(file_domain_name)
            created_at = datetime.now().isoformat()
            expires_at = expiry_date.isoformat() if expiry_date else None
            days_remaining = (expiry_date - datetime.now()).days if expiry_date else None
            
            # 更新元数据
            metadata = load_metadata(token_hash)
            
            # 移除旧记录 (如果是同一个域名)
            metadata = [r for r in metadata if r["domain"] != main_domain]
            
            new_record = {
                "domain": main_domain,
                "domains": req.domains,
                "created_at": created_at,
                "expires_at": expires_at,
                "days_remaining": days_remaining,
                "cert_path": f"{file_domain_name}/cert.pem",
                "key_path": f"{file_domain_name}/privkey.pem"
            }
            metadata.append(new_record)
            save_metadata(token_hash, metadata)
            
            logger.info("Task completed successfully and metadata updated.")
        else:
            logger.error("Certificate update failed.")
            
    except Exception as e:
        logger.error(f"Task failed: {e}")

# --- API 路由 ---

@app.post("/cert/apply")
async def apply_cert(
    req: ApplyRequest, 
    background_tasks: BackgroundTasks,
    token: str = Depends(get_current_user_token)
):
    """
    提交证书申请任务 (异步)
    """
    # 启动后台任务
    background_tasks.add_task(run_cert_update_task, token, req)
    
    return {
        "status": "pending",
        "message": "Certificate application started. Check status later via /cert/list"
    }

@app.get("/cert/list", response_model=List[CertRecord])
async def list_certs(token: str = Depends(get_current_user_token)):
    """
    列出当前 Token 下的所有证书
    """
    token_hash = get_token_hash(token)
    return load_metadata(token_hash)

@app.get("/cert/download/{domain}/{filename}")
async def download_cert(
    domain: str, 
    filename: str,
    token: str = Depends(get_current_user_token)
):
    """
    下载证书文件
    """
    # 安全校验：防止路径遍历
    if ".." in domain or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    token_hash = get_token_hash(token)
    user_dir = get_user_cert_dir(token_hash)
    file_path = user_dir / domain / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(file_path, filename=filename)
