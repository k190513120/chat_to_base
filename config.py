#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书API配置文件
请根据实际情况修改以下配置
"""

# 飞书应用配置
FEISHU_CONFIG = {
    # 应用ID
    "app_id": "cli_a757be749210500e",
    
    # 应用密钥
    "app_secret": "EvAyrNVzqxV7Wp3gET8oA5tjAt1T5ZfJ",
    
    # 多维表格链接
    "bitable_url": "https://larkcommunity.feishu.cn/base/O563bWgIwaIqy1sd9ulc15m6nCe?table=tblScOy4AiLem1EO&view=vewVlk8FaQ"
}

# API配置
API_CONFIG = {
    # 飞书开放平台API基础URL
    "base_url": "https://open.feishu.cn/open-apis",
    
    # 请求间隔时间（秒）
    "request_interval": 0.1,
    
    # 批量处理大小
    "batch_size": 500,
    
    # token提前刷新时间（秒）
    "token_refresh_advance": 300
}

# 日志配置
LOG_CONFIG = {
    # 日志级别
    "level": "INFO",
    
    # 日志文件名
    "filename": "feishu_sync.log",
    
    # 日志格式
    "format": "%(asctime)s - %(levelname)s - %(message)s"
}