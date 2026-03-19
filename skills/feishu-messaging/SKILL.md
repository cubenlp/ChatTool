# 飞书消息与文档 Skill

## 概述

此 Skill 提供了通过飞书 OpenAPI 进行消息发送、群聊创建与文档分享等功能，适用于通知、协作与信息分发场景。

## 核心能力

功能 状态 所需权限
发送文本消息✅ 可用 `im:message:send_as_bot `
发送富文本消息✅ 可用 `im:message:send_as_bot `
发送图片消息✅ 可用 `im:message:send_as_bot`
上传文件✅ 可用 `im:file`  


## 使用说明

### 发送消息给指定用户
    给 [姓名] 发一条飞书消息，告诉他 [内容]

前置条件：需要获取用户的 open_id

### 1. 获取群聊id的方法
    import json
    import requests

    url = "https://open.feishu.cn/open-apis/im/v1/chats"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN"
    }

    response = requests.get(url, headers=headers)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

### 2. 创建群聊（私聊可忽略）
    import requests
    import json

    url = "https://open.feishu.cn/open-apis/im/v1/chats"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
        "Content-Type": "application/json"
    }
    payload = {
        "name": "测试群聊",
        "chat_mode": "group",
        "description": "用于测试的群聊"
    }
    response = requests.post(url, headers=headers, json=payload)
    print(response.json())

### 3. 邀请用户进群（如果是群聊）
    import requests
    import json

    url = "https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/members"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
        "Content-Type": "application/json"
    }
    payload = {
        "id_list": ["open_id_1", "open_id_2"],
        "member_id_type": "open_id"
    }
    response = requests.post(url, headers=headers, json=payload)
    print(response.json())

### 4. 更新群名称
    import requests
    import json

    url = "https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
        "Content-Type": "application/json"
    }
    payload = {
        "name": "新群名称"
    }
    response = requests.patch(url, headers=headers, json=payload)
    print(response.json())

### 分享文档给用户或群聊
    将 [文档链接] 通过飞书分享给 [用户/群聊]

前置条件：已获取文档的 token 和 chat_id

### 1. 获取 user_id
    import requests
    import json

    url = "https://open.feishu.cn/open-apis/contact/v3/users?user_id_type=open_id&department_id=0"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN"
    }
    response = requests.get(url, headers=headers)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

### 2. 分享文档
    import requests
    import json

    url = "https://open.feishu.cn/open-apis/drive/v1/permissions/{file_token}/members"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
        "Content-Type": "application/json"
    }
    payload = {
        "member_type": "openid",
        "member_id": "ou_xxx",
        "perm": "view"
    }
    response = requests.post(url, headers=headers, json=payload)
    print(response.json())

## 注意事项

- 使用前确保机器人具备 `im:message:send_as_bot` 权限
- 使用的 Token 需来自企业自建应用
- 群聊消息发送需机器人已加入群
