#!/usr/bin/env python3
"""
GitHub Actions 触发脚本
用于通过API触发飞书群成员同步工作流
"""

import requests
import json
import sys

def trigger_github_action(bitable_url, chat_id, github_token="YOUR_GITHUB_TOKEN"):
    """
    触发GitHub Action工作流
    
    Args:
        bitable_url: 飞书多维表格URL
        chat_id: 飞书群ID
        github_token: GitHub访问令牌
    
    Returns:
        bool: 是否成功触发
    """
    url = "https://api.github.com/repos/k190513120/chat_to_base/actions/workflows/sync-feishu-members.yml/dispatches"
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    data = {
        "ref": "main",
        "inputs": {
            "bitable_url": bitable_url,
            "chat_id": chat_id
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 204:
            print("✅ GitHub Action 触发成功！")
            print(f"📊 多维表格URL: {bitable_url}")
            print(f"💬 群聊ID: {chat_id}")
            print("🔗 查看执行状态: https://github.com/k190513120/chat_to_base/actions")
            return True
        else:
            print(f"❌ 触发失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

def get_workflow_runs(github_token="YOUR_GITHUB_TOKEN", limit=5):
    """
    获取工作流运行记录
    
    Args:
        github_token: GitHub访问令牌
        limit: 返回记录数量限制
    
    Returns:
        list: 工作流运行记录
    """
    url = "https://api.github.com/repos/k190513120/chat_to_base/actions/workflows/sync-feishu-members.yml/runs"
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    params = {
        "per_page": limit
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            runs = data.get("workflow_runs", [])
            
            print(f"📋 最近 {len(runs)} 次工作流运行记录:")
            print("-" * 80)
            
            for i, run in enumerate(runs, 1):
                status = run.get("status", "unknown")
                conclusion = run.get("conclusion", "")
                created_at = run.get("created_at", "")
                html_url = run.get("html_url", "")
                
                # 状态图标
                if conclusion == "success":
                    status_icon = "✅"
                elif conclusion == "failure":
                    status_icon = "❌"
                elif status == "in_progress":
                    status_icon = "🔄"
                else:
                    status_icon = "⏸️"
                
                print(f"{i}. {status_icon} 状态: {status}")
                if conclusion:
                    print(f"   结果: {conclusion}")
                print(f"   时间: {created_at}")
                print(f"   链接: {html_url}")
                print()
            
            return runs
        else:
            print(f"❌ 获取工作流记录失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return []

def main():
    """主函数"""
    if len(sys.argv) == 1:
        print("📖 使用说明:")
        print("触发工作流:")
        print("  python trigger_github_action.py <bitable_url> <chat_id>")
        print()
        print("查看运行状态:")
        print("  python trigger_github_action.py --status")
        print()
        print("示例:")
        print("  python trigger_github_action.py \"https://bytedance.feishu.cn/base/base_id?table=table_id\" \"oc_chat_id\"")
        return
    
    if len(sys.argv) == 2 and sys.argv[1] == "--status":
        # 查看工作流状态
        get_workflow_runs()
        return
    
    if len(sys.argv) != 3:
        print("❌ 参数错误！")
        print("使用方法: python trigger_github_action.py <bitable_url> <chat_id>")
        print("或者: python trigger_github_action.py --status")
        return
    
    bitable_url = sys.argv[1]
    chat_id = sys.argv[2]
    
    # 验证参数
    if not bitable_url.startswith("https://"):
        print("❌ 多维表格URL格式错误，应以 https:// 开头")
        return
    
    if not chat_id.startswith("oc_"):
        print("❌ 群聊ID格式错误，应以 oc_ 开头")
        return
    
    # 触发工作流
    success = trigger_github_action(bitable_url, chat_id)
    
    if success:
        print("\n⏳ 工作流已开始执行，请稍等片刻后查看状态...")
        print("💡 提示：可以使用 'python trigger_github_action.py --status' 查看执行状态")

if __name__ == "__main__":
    main()