#!/usr/bin/env python3
"""
飞书群成员同步 HTTP API 服务
提供RESTful接口调用飞书群成员同步功能
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from feishu_group_members import FeishuAPI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api_server.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="飞书群成员同步API",
    description="提供飞书群成员信息同步到多维表格的HTTP接口",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class SyncRequest(BaseModel):
    bitable_url: str = Field(..., description="飞书多维表格URL")
    chat_id: str = Field(..., description="飞书群ID")
    app_id: str = Field(None, description="飞书应用ID（可选，优先使用环境变量）")
    app_secret: str = Field(None, description="飞书应用密钥（可选，优先使用环境变量）")

class SyncResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = None
    task_id: str = None

# 任务状态存储
task_status = {}

def get_feishu_config(request: SyncRequest) -> tuple:
    """获取飞书配置"""
    app_id = request.app_id or os.getenv('FEISHU_APP_ID')
    app_secret = request.app_secret or os.getenv('FEISHU_APP_SECRET')
    
    if not app_id or not app_secret:
        raise HTTPException(
            status_code=400, 
            detail="飞书应用ID和密钥未配置，请在请求中提供或设置环境变量 FEISHU_APP_ID 和 FEISHU_APP_SECRET"
        )
    
    return app_id, app_secret

async def sync_members_task(task_id: str, bitable_url: str, chat_id: str, app_id: str, app_secret: str):
    """异步执行同步任务"""
    try:
        task_status[task_id] = {
            "status": "running",
            "message": "正在同步群成员信息...",
            "start_time": datetime.now().isoformat(),
            "progress": 0
        }
        
        # 创建API实例
        api = FeishuAPI(app_id, app_secret)
        
        # 解析多维表格URL
        app_token, table_id = api.parse_bitable_url(bitable_url)
        task_status[task_id]["progress"] = 10
        
        # 获取访问令牌
        api.get_tenant_access_token()
        task_status[task_id]["progress"] = 20
        
        # 获取表格字段
        fields = api.get_bitable_fields(app_token, table_id)
        task_status[task_id]["progress"] = 30
        
        # 查找目标字段
        personnel_fields = [f for f in fields if f.get("type") == 11]
        text_fields = [f for f in fields if f.get("type") == 1]
        
        target_fields = {}
        
        # 查找人员字段
        if personnel_fields:
            target_fields["member"] = personnel_fields[0]
        elif text_fields:
            target_fields["member"] = text_fields[0]
        
        # 查找群名称字段
        chat_name_fields = [f for f in text_fields if "群" in f.get("field_name", "") or "名称" in f.get("field_name", "")]
        if chat_name_fields:
            target_fields["chat_name"] = chat_name_fields[0]
        elif len(text_fields) > 1:
            target_fields["chat_name"] = text_fields[1]
        
        # 查找租户字段
        tenant_fields = [f for f in text_fields if "租户" in f.get("field_name", "") or "tenant" in f.get("field_name", "").lower()]
        if tenant_fields:
            target_fields["tenant"] = tenant_fields[0]
        elif len(text_fields) > 2:
            target_fields["tenant"] = text_fields[2]
        
        task_status[task_id]["progress"] = 40
        
        # 获取群聊信息
        chat_info = api.get_chat_info(chat_id)
        chat_name = chat_info.get("name", "未知群聊")
        task_status[task_id]["progress"] = 50
        
        # 获取群成员
        members = api.get_chat_members(chat_id)
        task_status[task_id]["progress"] = 70
        
        if not members:
            raise Exception("未获取到任何群成员")
        
        # 准备记录
        records = []
        for member in members:
            member_id = member.get("member_id")
            if not member_id:
                continue
                
            member_tenant_key = member.get("tenant_key", "")
            fields_data = {}
            
            # 成员字段
            member_field = target_fields.get("member")
            if member_field:
                if member_field.get("type") == 11:
                    fields_data[member_field.get("field_name")] = [{"id": member_id}]
                else:
                    fields_data[member_field.get("field_name")] = member_id
            
            # 群名称字段
            chat_name_field = target_fields.get("chat_name")
            if chat_name_field:
                fields_data[chat_name_field.get("field_name")] = chat_name
                
            # 租户字段
            tenant_field = target_fields.get("tenant")
            if tenant_field and member_tenant_key:
                fields_data[tenant_field.get("field_name")] = member_tenant_key
            
            records.append({"fields": fields_data})
        
        task_status[task_id]["progress"] = 80
        
        # 写入多维表格
        success = api.add_bitable_records(app_token, table_id, records)
        
        if success:
            task_status[task_id] = {
                "status": "completed",
                "message": f"成功同步 {len(records)} 个群成员到多维表格",
                "start_time": task_status[task_id]["start_time"],
                "end_time": datetime.now().isoformat(),
                "progress": 100,
                "data": {
                    "chat_name": chat_name,
                    "member_count": len(records),
                    "fields_used": list(target_fields.keys())
                }
            }
        else:
            raise Exception("写入多维表格失败")
            
    except Exception as e:
        logger.error(f"同步任务失败: {e}")
        task_status[task_id] = {
            "status": "failed",
            "message": f"同步失败: {str(e)}",
            "start_time": task_status[task_id].get("start_time"),
            "end_time": datetime.now().isoformat(),
            "progress": 0
        }

@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "name": "飞书群成员同步API",
        "version": "1.0.0",
        "description": "提供飞书群成员信息同步到多维表格的HTTP接口",
        "endpoints": {
            "POST /sync": "同步群成员信息（异步）",
            "POST /sync/immediate": "同步群成员信息（同步）",
            "GET /task/{task_id}": "查询任务状态",
            "GET /health": "健康检查"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/sync", response_model=SyncResponse)
async def sync_members_async(request: SyncRequest, background_tasks: BackgroundTasks):
    """异步同步群成员信息到多维表格"""
    try:
        app_id, app_secret = get_feishu_config(request)
        
        # 生成任务ID
        task_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.chat_id) % 10000}"
        
        # 启动后台任务
        background_tasks.add_task(
            sync_members_task, 
            task_id, 
            request.bitable_url, 
            request.chat_id, 
            app_id, 
            app_secret
        )
        
        return SyncResponse(
            success=True,
            message="同步任务已启动",
            task_id=task_id
        )
        
    except Exception as e:
        logger.error(f"启动同步任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/immediate", response_model=SyncResponse)
async def sync_members_immediate(request: SyncRequest):
    """同步同步群成员信息到多维表格"""
    try:
        app_id, app_secret = get_feishu_config(request)
        
        # 创建API实例
        api = FeishuAPI(app_id, app_secret)
        
        # 解析多维表格URL
        app_token, table_id = api.parse_bitable_url(request.bitable_url)
        
        # 获取访问令牌
        api.get_tenant_access_token()
        
        # 获取表格字段
        fields = api.get_bitable_fields(app_token, table_id)
        
        # 查找目标字段（简化版本）
        personnel_fields = [f for f in fields if f.get("type") == 11]
        text_fields = [f for f in fields if f.get("type") == 1]
        
        target_fields = {}
        if personnel_fields:
            target_fields["member"] = personnel_fields[0]
        elif text_fields:
            target_fields["member"] = text_fields[0]
        
        # 获取群聊信息
        chat_info = api.get_chat_info(request.chat_id)
        chat_name = chat_info.get("name", "未知群聊")
        
        # 获取群成员
        members = api.get_chat_members(request.chat_id)
        
        if not members:
            raise HTTPException(status_code=404, detail="未获取到任何群成员")
        
        # 准备记录（简化版本）
        records = []
        for member in members:
            member_id = member.get("member_id")
            if not member_id:
                continue
                
            fields_data = {}
            member_field = target_fields.get("member")
            if member_field:
                if member_field.get("type") == 11:
                    fields_data[member_field.get("field_name")] = [{"id": member_id}]
                else:
                    fields_data[member_field.get("field_name")] = member_id
            
            records.append({"fields": fields_data})
        
        # 写入多维表格
        success = api.add_bitable_records(app_token, table_id, records)
        
        if success:
            return SyncResponse(
                success=True,
                message=f"成功同步 {len(records)} 个群成员到多维表格",
                data={
                    "chat_name": chat_name,
                    "member_count": len(records)
                }
            )
        else:
            raise HTTPException(status_code=500, detail="写入多维表格失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task_status[task_id]

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)