#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API工具模块

提供API调用的通用工具和辅助函数。
"""

import json
import time
import requests
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

def make_api_request(url: str, method: str = "GET", headers: Dict[str, str] = None, 
                    params: Dict[str, Any] = None, data: Dict[str, Any] = None, 
                    json_data: Dict[str, Any] = None, retry_count: int = 3, 
                    retry_delay: int = 2) -> Optional[Dict[str, Any]]:
    """
    发送API请求，支持重试机制
    
    Args:
        url: API端点URL
        method: HTTP方法（GET, POST, PUT等）
        headers: 请求头
        params: URL参数
        data: 表单数据
        json_data: JSON数据
        retry_count: 重试次数
        retry_delay: 重试延迟（秒）
        
    Returns:
        dict: API响应数据，请求失败返回None
    """
    method = method.upper()
    headers = headers or {}
    
    for attempt in range(retry_count):
        try:
            logger.debug(f"API请求: {method} {url}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                timeout=30
            )
            
            # 检查响应
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    # 非JSON响应
                    return {"text": response.text, "status": response.status_code}
            else:
                logger.warning(f"API请求失败: {response.status_code} - {response.text}")
                # 处理特定错误码
                if response.status_code == 429:  # 速率限制
                    if attempt < retry_count - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.info(f"遇到速率限制，等待 {wait_time} 秒后重试")
                        time.sleep(wait_time)
                        continue
                elif response.status_code >= 500:  # 服务器错误
                    if attempt < retry_count - 1:
                        logger.info(f"服务器错误，第 {attempt+1} 次重试")
                        time.sleep(retry_delay)
                        continue
                
                return None
                
        except requests.RequestException as e:
            logger.error(f"API请求异常: {e}")
            if attempt < retry_count - 1:
                logger.info(f"第 {attempt+1} 次重试")
                time.sleep(retry_delay)
            else:
                return None
    
    return None

def get_x_api_token_info(api_key: str, api_secret: str, access_token: str, 
                        access_token_secret: str) -> Dict[str, Any]:
    """
    获取X API令牌信息
    
    Args:
        api_key: API密钥
        api_secret: API密钥密文
        access_token: 访问令牌
        access_token_secret: 访问令牌密文
        
    Returns:
        dict: 令牌信息
    """
    import tweepy
    
    try:
        # 创建认证对象
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret, access_token, access_token_secret
        )
        
        # 创建API客户端
        api = tweepy.API(auth)
        
        # 获取账户信息验证令牌有效性
        user = api.verify_credentials()
        
        return {
            "valid": True,
            "user_id": user.id_str,
            "screen_name": user.screen_name,
            "name": user.name,
            "expires": "未过期"  # OAuth1不设置过期时间
        }
        
    except Exception as e:
        logger.error(f"获取X API令牌信息失败: {e}")
        return {
            "valid": False,
            "error": str(e)
        }

def check_deepseek_api_key(api_key: str) -> Dict[str, Any]:
    """
    检查DeepSeek API密钥有效性
    
    Args:
        api_key: DeepSeek API密钥
        
    Returns:
        dict: 检查结果
    """
    url = "https://api.deepseek.com/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = make_api_request(url, headers=headers)
        
        if response and "data" in response:
            return {
                "valid": True,
                "models": [model.get("id") for model in response.get("data", [])]
            }
        else:
            return {
                "valid": False,
                "error": "无法获取模型列表，API密钥可能无效"
            }
            
    except Exception as e:
        logger.error(f"检查DeepSeek API密钥失败: {e}")
        return {
            "valid": False,
            "error": str(e)
        }