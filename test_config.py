#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置测试脚本
用于验证飞书API配置是否正确
"""

import requests
import json
from urllib.parse import urlparse, parse_qs
from config import FEISHU_CONFIG, API_CONFIG

def test_app_credentials():
    """测试应用凭证是否有效"""
    print("🔍 测试应用凭证...")
    
    url = f"{API_CONFIG['base_url']}/auth/v3/tenant_access_token/internal/"
    payload = {
        "app_id": FEISHU_CONFIG["app_id"],
        "app_secret": FEISHU_CONFIG["app_secret"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0:
            print("✅ 应用凭证有效")
            return data["tenant_access_token"]
        else:
            print(f"❌ 应用凭证无效: {data.get('msg', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ 测试应用凭证失败: {e}")
        return None

def test_bitable_url():
    """测试多维表格URL是否有效"""
    print("\n🔍 测试多维表格URL...")
    
    try:
        url = FEISHU_CONFIG["bitable_url"]
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # 提取app_token
        app_token = None
        for i, part in enumerate(path_parts):
            if part == 'base' and i + 1 < len(path_parts):
                app_token = path_parts[i + 1]
                break
        
        # 提取table_id
        query_params = parse_qs(parsed.query)
        table_id = query_params.get('table', [None])[0]
        
        if app_token and table_id:
            print(f"✅ URL解析成功")
            print(f"   App Token: {app_token}")
            print(f"   Table ID: {table_id}")
            return app_token, table_id
        else:
            print("❌ URL格式不正确，无法提取app_token或table_id")
            return None, None
            
    except Exception as e:
        print(f"❌ URL解析失败: {e}")
        return None, None

def test_bitable_access(token, app_token, table_id):
    """测试多维表格访问权限"""
    print("\n🔍 测试多维表格访问权限...")
    
    if not token or not app_token or not table_id:
        print("❌ 缺少必要参数，跳过测试")
        return False
    
    url = f"{API_CONFIG['base_url']}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0:
            fields = data.get("data", {}).get("items", [])
            print(f"✅ 多维表格访问成功，共有 {len(fields)} 个字段")
            
            # 检查字段类型
            person_fields = [f for f in fields if f.get("type") == 11]
            text_fields = [f for f in fields if f.get("type") == 1]
            
            if person_fields:
                print(f"   找到 {len(person_fields)} 个人员字段")
                for field in person_fields:
                    print(f"   - {field.get('field_name', '未知字段')}")
            elif text_fields:
                print(f"   找到 {len(text_fields)} 个文本字段（可作为备选）")
                for field in text_fields[:3]:  # 只显示前3个
                    print(f"   - {field.get('field_name', '未知字段')}")
            else:
                print("   ⚠️  未找到人员字段或文本字段")
            
            return True
        else:
            print(f"❌ 多维表格访问失败: {data.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试多维表格访问失败: {e}")
        return False

def test_chat_permission(token):
    """测试群聊权限"""
    print("\n🔍 测试群聊权限...")
    
    if not token:
        print("❌ 缺少token，跳过测试")
        return False
    
    url = f"{API_CONFIG['base_url']}/im/v1/chats"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {"page_size": 1}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0:
            print("✅ 群聊权限正常")
            return True
        else:
            print(f"❌ 群聊权限不足: {data.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试群聊权限失败: {e}")
        return False

def main():
    """主函数"""
    print("飞书API配置测试工具")
    print("=" * 50)
    
    # 显示当前配置
    print(f"App ID: {FEISHU_CONFIG['app_id']}")
    print(f"App Secret: {'*' * (len(FEISHU_CONFIG['app_secret']) - 4) + FEISHU_CONFIG['app_secret'][-4:]}")
    print(f"多维表格URL: {FEISHU_CONFIG['bitable_url']}")
    print()
    
    # 测试应用凭证
    token = test_app_credentials()
    
    # 测试多维表格URL
    app_token, table_id = test_bitable_url()
    
    # 测试多维表格访问权限
    bitable_ok = test_bitable_access(token, app_token, table_id)
    
    # 测试群聊权限
    chat_ok = test_chat_permission(token)
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    
    if token:
        print("✅ 应用凭证: 正常")
    else:
        print("❌ 应用凭证: 异常")
    
    if app_token and table_id:
        print("✅ 多维表格URL: 正常")
    else:
        print("❌ 多维表格URL: 异常")
    
    if bitable_ok:
        print("✅ 多维表格权限: 正常")
    else:
        print("❌ 多维表格权限: 异常")
    
    if chat_ok:
        print("✅ 群聊权限: 正常")
    else:
        print("❌ 群聊权限: 异常")
    
    if token and app_token and table_id and bitable_ok and chat_ok:
        print("\n🎉 所有配置测试通过！可以正常使用脚本。")
    else:
        print("\n⚠️  存在配置问题，请检查：")
        if not token:
            print("   - 检查App ID和App Secret是否正确")
        if not (app_token and table_id):
            print("   - 检查多维表格URL格式是否正确")
        if not bitable_ok:
            print("   - 检查应用是否有多维表格访问权限")
        if not chat_ok:
            print("   - 检查应用是否有群聊访问权限")

if __name__ == "__main__":
    main()