#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书群成员同步到多维表格
支持自动获取群成员信息并写入到指定的多维表格中
"""

import sys
import os
import requests
import json
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs
from config import FEISHU_CONFIG, API_CONFIG, LOG_CONFIG

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG["level"]),
    format=LOG_CONFIG["format"],
    handlers=[
        logging.FileHandler(LOG_CONFIG["filename"], encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FeishuAPI:
    """飞书API客户端"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = API_CONFIG["base_url"]
        self.tenant_access_token = None
        self.token_expire_time = 0
        
    def get_tenant_access_token(self) -> str:
        """获取tenant_access_token"""
        current_time = time.time()
        
        # 如果token还未过期，直接返回
        if self.tenant_access_token and current_time < self.token_expire_time:
            return self.tenant_access_token
            
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal/"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                self.tenant_access_token = data["tenant_access_token"]
                # 设置过期时间（提前5分钟刷新）
                self.token_expire_time = current_time + data.get("expire", 7200) - API_CONFIG["token_refresh_advance"]
                logger.info("成功获取tenant_access_token")
                return self.tenant_access_token
            else:
                raise Exception(f"获取token失败: {data.get('msg', '未知错误')}")
                
        except Exception as e:
            logger.error(f"获取tenant_access_token失败: {e}")
            raise
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        token = self.get_tenant_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_chat_info(self, chat_id: str) -> Dict:
        """获取群聊详细信息"""
        url = f"{self.base_url}/im/v1/chats/{chat_id}"
        headers = self.get_headers()
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                return data.get("data", {})
            else:
                logger.warning(f"获取群聊信息失败: {data.get('msg', '未知错误')}")
                return {}
                
        except Exception as e:
            logger.warning(f"获取群聊信息异常: {e}")
            return {}

    def get_chat_members(self, chat_id: str) -> List[Dict]:
        """获取群成员列表"""
        url = f"{self.base_url}/im/v1/chats/{chat_id}/members"
        headers = self.get_headers()
        all_members = []
        page_token = None
        
        try:
            while True:
                params = {"page_size": 100}
                if page_token:
                    params["page_token"] = page_token
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") != 0:
                    raise Exception(f"获取群成员失败: {data.get('msg', '未知错误')}")
                
                members = data.get("data", {}).get("items", [])
                all_members.extend(members)
                
                # 检查是否还有下一页
                page_token = data.get("data", {}).get("page_token")
                if not page_token:
                    break
                    
                logger.info(f"已获取 {len(all_members)} 个群成员")
                time.sleep(API_CONFIG["request_interval"])  # 避免请求过快
            
            logger.info(f"总共获取到 {len(all_members)} 个群成员")
            return all_members
            
        except Exception as e:
            logger.error(f"获取群成员失败: {e}")
            raise
    

    
    def parse_bitable_url(self, url: str) -> tuple:
        """解析多维表格URL，提取app_token和table_id"""
        try:
            # 解析URL
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            # 从路径中提取app_token
            app_token = None
            for i, part in enumerate(path_parts):
                if part == 'base' and i + 1 < len(path_parts):
                    app_token = path_parts[i + 1]
                    break
            
            # 从查询参数中提取table_id
            query_params = parse_qs(parsed.query)
            table_id = query_params.get('table', [None])[0]
            
            if not app_token or not table_id:
                raise ValueError("无法从URL中提取app_token或table_id")
                
            return app_token, table_id
            
        except Exception as e:
            logger.error(f"解析多维表格URL失败: {e}")
            raise
    
    def get_bitable_fields(self, app_token: str, table_id: str) -> List[Dict]:
        """获取多维表格字段信息"""
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        headers = self.get_headers()
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                fields = data.get("data", {}).get("items", [])
                logger.info(f"获取到 {len(fields)} 个字段")
                return fields
            else:
                raise Exception(f"获取字段信息失败: {data.get('msg', '未知错误')}")
                
        except Exception as e:
            logger.error(f"获取字段信息失败: {e}")
            raise
    
    def add_bitable_records(self, app_token: str, table_id: str, records: List[Dict]) -> bool:
        """批量添加多维表格记录"""
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        headers = self.get_headers()
        
        # 分批处理，每次最多500条记录
        batch_size = API_CONFIG["batch_size"]
        total_records = len(records)
        
        try:
            for i in range(0, total_records, batch_size):
                batch_records = records[i:i + batch_size]
                payload = {"records": batch_records}
                
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") == 0:
                    logger.info(f"成功添加第 {i//batch_size + 1} 批记录 ({len(batch_records)} 条)")
                else:
                    logger.error(f"添加第 {i//batch_size + 1} 批记录失败: {data.get('msg', '未知错误')}")
                    return False
                
                time.sleep(0.2)  # 避免请求过快
            
            logger.info(f"所有记录添加完成，总计 {total_records} 条")
            return True
            
        except Exception as e:
            logger.error(f"添加记录失败: {e}")
            return False

def main():
    """主函数"""
    # 从配置文件读取配置信息
    APP_ID = FEISHU_CONFIG["app_id"]
    APP_SECRET = FEISHU_CONFIG["app_secret"]
    
    # 获取多维表格URL - 优先使用命令行参数，其次使用配置文件
    BITABLE_URL = None
    if len(sys.argv) > 1:
        BITABLE_URL = sys.argv[1].strip()
    elif "bitable_url" in FEISHU_CONFIG:
        BITABLE_URL = FEISHU_CONFIG["bitable_url"]
    
    if not BITABLE_URL:
        logger.error("未提供多维表格URL，请通过命令行参数或配置文件提供")
        return
    
    # 获取群ID - 从标准输入读取
    chat_id = input("请输入飞书群ID: ").strip()
    if not chat_id:
        logger.error("群ID不能为空")
        return
    
    try:
        # 初始化API客户端
        api = FeishuAPI(APP_ID, APP_SECRET)
        
        # 解析多维表格URL
        app_token, table_id = api.parse_bitable_url(BITABLE_URL)
        logger.info(f"解析得到 app_token: {app_token}, table_id: {table_id}")
        
        # 获取多维表格字段信息
        fields = api.get_bitable_fields(app_token, table_id)
        
        # 查找各种类型的字段
        person_fields = [f for f in fields if f.get("type") == 11]  # 11是人员字段类型
        text_fields = [f for f in fields if f.get("type") == 1]     # 1是文本字段类型
        
        # 确定要使用的字段
        target_fields = {}
        
        # 人员字段（优先）
        if person_fields:
            target_fields["member"] = person_fields[0]
            logger.info(f"找到人员字段: {target_fields['member'].get('field_name')}")
        elif text_fields:
            target_fields["member"] = text_fields[0]
            logger.info(f"将使用文本字段存储成员: {target_fields['member'].get('field_name')}")
        else:
            logger.error("未找到合适的字段来存储成员信息")
            return
            
        # 查找群名称字段
        chat_name_fields = [f for f in text_fields if "群" in f.get("field_name", "") or "名称" in f.get("field_name", "")]
        if chat_name_fields:
            target_fields["chat_name"] = chat_name_fields[0]
            logger.info(f"找到群名称字段: {target_fields['chat_name'].get('field_name')}")
        elif len(text_fields) > 1:
            target_fields["chat_name"] = text_fields[1]
            logger.info(f"将使用文本字段存储群名称: {target_fields['chat_name'].get('field_name')}")
            
        # 查找租户字段
        tenant_fields = [f for f in text_fields if "租户" in f.get("field_name", "") or "tenant" in f.get("field_name", "").lower()]
        if tenant_fields:
            target_fields["tenant"] = tenant_fields[0]
            logger.info(f"找到租户字段: {target_fields['tenant'].get('field_name')}")
        elif len(text_fields) > 2:
            target_fields["tenant"] = text_fields[2]
            logger.info(f"将使用文本字段存储租户信息: {target_fields['tenant'].get('field_name')}")
        
        # 获取群聊信息
        logger.info("开始获取群聊信息...")
        chat_info = api.get_chat_info(chat_id)
        chat_name = chat_info.get("name", "未知群聊")
        # 从群聊信息中获取tenant_key
        chat_tenant_key = chat_info.get("tenant_key", "")
        logger.info(f"群聊信息: 名称={chat_name}, 租户ID={chat_tenant_key}")
        
        # 获取群成员
        logger.info("开始获取群成员信息...")
        members = api.get_chat_members(chat_id)
        
        if not members:
            logger.warning("未获取到任何群成员")
            return
        
        # 准备写入多维表格的记录
        records = []
        for member in members:
            member_id = member.get("member_id")
            if not member_id:
                continue
                
            # 从群成员API返回的数据中获取tenant_key
            member_tenant_key = member.get("tenant_key", "")
                
            # 构建记录字段
            fields_data = {}
            
            # 成员字段
            member_field = target_fields.get("member")
            if member_field:
                if member_field.get("type") == 11:  # 人员字段
                    fields_data[member_field.get("field_name")] = [{"id": member_id}]
                else:  # 文本字段
                    fields_data[member_field.get("field_name")] = member_id
            
            # 群名称字段
            chat_name_field = target_fields.get("chat_name")
            if chat_name_field:
                fields_data[chat_name_field.get("field_name")] = chat_name
                
            # 租户字段 - 使用群成员API返回的tenant_key
            tenant_field = target_fields.get("tenant")
            if tenant_field and member_tenant_key:
                fields_data[tenant_field.get("field_name")] = member_tenant_key
            
            record = {"fields": fields_data}
            records.append(record)
            time.sleep(API_CONFIG["request_interval"] / 2)  # 避免请求过快
        
        if not records:
            logger.warning("没有有效的记录可以写入")
            return
        
        # 写入多维表格
        logger.info(f"开始写入 {len(records)} 条记录到多维表格...")
        success = api.add_bitable_records(app_token, table_id, records)
        
        if success:
            logger.info("✅ 群成员信息已成功写入多维表格！")
        else:
            logger.error("❌ 写入多维表格失败")
            
    except Exception as e:
        logger.error(f"程序执行失败: {e}")

if __name__ == "__main__":
    main()