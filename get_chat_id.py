#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取飞书群ID的辅助脚本
帮助用户查找和获取目标群的chat_id
"""

import requests
import json
import logging
from config import FEISHU_CONFIG, API_CONFIG, LOG_CONFIG

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG["level"]),
    format=LOG_CONFIG["format"]
)
logger = logging.getLogger(__name__)

class FeishuChatHelper:
    """飞书群聊辅助工具"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = API_CONFIG["base_url"]
        self.tenant_access_token = None
    
    def get_tenant_access_token(self) -> str:
        """获取tenant_access_token"""
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
                logger.info("成功获取tenant_access_token")
                return self.tenant_access_token
            else:
                raise Exception(f"获取token失败: {data.get('msg', '未知错误')}")
                
        except Exception as e:
            logger.error(f"获取tenant_access_token失败: {e}")
            raise
    
    def get_headers(self) -> dict:
        """获取请求头"""
        if not self.tenant_access_token:
            self.get_tenant_access_token()
        
        return {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }
    
    def get_chat_list(self) -> list:
        """获取群列表"""
        url = f"{self.base_url}/im/v1/chats"
        headers = self.get_headers()
        all_chats = []
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
                    raise Exception(f"获取群列表失败: {data.get('msg', '未知错误')}")
                
                chats = data.get("data", {}).get("items", [])
                all_chats.extend(chats)
                
                # 检查是否还有下一页
                page_token = data.get("data", {}).get("page_token")
                if not page_token:
                    break
            
            logger.info(f"总共获取到 {len(all_chats)} 个群")
            return all_chats
            
        except Exception as e:
            logger.error(f"获取群列表失败: {e}")
            raise
    
    def search_chats_by_name(self, keyword: str) -> list:
        """根据群名称关键词搜索群"""
        chats = self.get_chat_list()
        matched_chats = []
        
        for chat in chats:
            chat_name = chat.get("name", "")
            if keyword.lower() in chat_name.lower():
                matched_chats.append(chat)
        
        return matched_chats
    
    def display_chats(self, chats: list):
        """显示群信息"""
        if not chats:
            print("未找到匹配的群")
            return
        
        print(f"\n找到 {len(chats)} 个匹配的群：")
        print("-" * 80)
        print(f"{'序号':<4} {'群名称':<30} {'群ID':<25} {'成员数':<8}")
        print("-" * 80)
        
        for i, chat in enumerate(chats, 1):
            chat_id = chat.get("chat_id", "")
            chat_name = chat.get("name", "未知群名")
            member_count = chat.get("member_count", 0)
            
            # 截断过长的群名称
            if len(chat_name) > 28:
                chat_name = chat_name[:25] + "..."
            
            print(f"{i:<4} {chat_name:<30} {chat_id:<25} {member_count:<8}")
        
        print("-" * 80)

def main():
    """主函数"""
    print("飞书群ID获取工具")
    print("=" * 50)
    
    try:
        # 初始化API客户端
        helper = FeishuChatHelper(
            FEISHU_CONFIG["app_id"],
            FEISHU_CONFIG["app_secret"]
        )
        
        while True:
            print("\n请选择操作：")
            print("1. 获取所有群列表")
            print("2. 根据群名称搜索")
            print("3. 退出")
            
            choice = input("\n请输入选项 (1-3): ").strip()
            
            if choice == "1":
                print("\n正在获取所有群列表...")
                chats = helper.get_chat_list()
                helper.display_chats(chats)
                
            elif choice == "2":
                keyword = input("\n请输入群名称关键词: ").strip()
                if keyword:
                    print(f"\n正在搜索包含 '{keyword}' 的群...")
                    matched_chats = helper.search_chats_by_name(keyword)
                    helper.display_chats(matched_chats)
                else:
                    print("关键词不能为空")
                    
            elif choice == "3":
                print("退出程序")
                break
                
            else:
                print("无效选项，请重新选择")
    
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"\n错误: {e}")
        print("\n请检查：")
        print("1. 应用配置是否正确")
        print("2. 应用是否有 im:chat 权限")
        print("3. 网络连接是否正常")

if __name__ == "__main__":
    main()