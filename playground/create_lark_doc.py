#!/usr/bin/env python3
"""创建飞书文档：小王的养虾笔记"""
import os
import json

os.environ['https_proxy'] = 'http://127.0.0.1:1082'

import lark_oapi as lark
from lark_oapi.api.docx.v1 import CreateDocumentRequest, CreateDocumentRequestBody

# 使用 cc-connect 配置
APP_ID = "cli_a923e9ff98b91bc8"
APP_SECRET = "UjEvABdvjAhwynPnwyfsYgckaFgC6QKQ"

client = lark.Client.builder() \
    .app_id(APP_ID) \
    .app_secret(APP_SECRET) \
    .log_level(lark.LogLevel.INFO) \
    .build()

# 创建文档
request = CreateDocumentRequest.builder() \
    .request_body(
        CreateDocumentRequestBody.builder()
        .title("小王的养虾笔记")
        .folder_token("")  # 空表示创建在根目录
        .build()
    ) \
    .build()

response = client.docx.v1.document.create(request)

if response.success():
    doc = response.data.document
    print(f"✅ 文档创建成功！")
    print(f"文档标题: {doc.title}")
    print(f"文档 ID: {doc.document_id}")
    print(f"文档链接: https://feishu.cn/docx/{doc.document_id}")

    # 保存文档信息
    with open("/Users/rexwzh/workspace/python/ChatTool/playground/lark_doc_info.json", "w") as f:
        json.dump({
            "title": doc.title,
            "document_id": doc.document_id,
            "url": f"https://feishu.cn/docx/{doc.document_id}"
        }, f, indent=2, ensure_ascii=False)
else:
    print(f"❌ 创建失败: code={response.code}, msg={response.msg}")
