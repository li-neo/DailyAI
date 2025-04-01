#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek分析器

使用DeepSeek API对收集的推文进行分析，生成技术报告。
"""

import json
import requests
from typing import List
from models.tweet import Tweet
from utils.logger import get_logger

class DeepSeekAnalyzer:
    """
    DeepSeek分析器
    
    使用DeepSeek的大语言模型API分析推文内容，生成洞察和趋势报告。
    """
    
    def __init__(self, api_config, deepseek_config):
        """
        初始化DeepSeek分析器
        
        Args:
            api_config: DeepSeek API配置
            deepseek_config: DeepSeek分析配置
        """
        self.api_key = api_config.get('api_key')
        self.org_id = api_config.get('organization_id')
        self.max_tokens = deepseek_config.get('max_token_count', 8000)
        self.temperature = deepseek_config.get('temperature', 0.7)
        self.logger = get_logger(__name__)
        
    def analyze(self, tweets: List[Tweet]) -> str:
        """
        分析推文集合，生成综合报告
        
        Args:
            tweets: 排序后的推文列表
            
        Returns:
            str: 分析报告
        """
        if not tweets:
            return "没有推文可供分析"
            
        self.logger.info(f"开始使用DeepSeek分析 {len(tweets)} 条推文")
        
        try:
            # 准备分析提示
            prompt = self._prepare_prompt(tweets)
            
            # 调用DeepSeek API
            response = self._call_api(prompt)
            
            if response:
                self.logger.info("DeepSeek分析完成")
                return response
            else:
                self.logger.error("DeepSeek分析失败")
                return "DeepSeek分析失败，请检查API配置或重试"
                
        except Exception as e:
            self.logger.error(f"DeepSeek分析出错: {e}")
            return f"分析过程中出错: {str(e)}"
    
    def _prepare_prompt(self, tweets: List[Tweet]) -> str:
        """
        准备分析提示
        
        Args:
            tweets: 推文列表
            
        Returns:
            str: 分析提示
        """
        # 整理推文内容
        tweets_content = []
        for i, tweet in enumerate(tweets, 1):
            date_str = tweet.created_at.strftime('%Y-%m-%d') if hasattr(tweet.created_at, 'strftime') else str(tweet.created_at)
            tweets_content.append(f"推文 {i}:\n作者: {tweet.author_fullname} (@{tweet.author})\n日期: {date_str}\n内容: {tweet.content}\nURL: {tweet.url}\n")
        
        tweets_text = "\n".join(tweets_content)
        
        # 构建提示
        prompt = f"""你是一位专业的AI技术分析师，请分析以下关于人工智能领域的推文，并生成一份详细的技术报告。

这些推文来自AI领域的知名专家和技术领袖，代表了当前AI技术的前沿发展和趋势。

请从以下几个方面进行分析：
1. 总体概述：总结这些推文反映的AI领域最新动态和热点
2. 技术趋势：识别这些推文中提到的新兴技术趋势和重要突破
3. 研究方向：分析当前AI研究的主要方向和重点关注领域
4. 产业影响：评估这些技术进展对产业和应用的潜在影响
5. 专家观点：提炼出这些AI领域专家的独特观点和见解

以下是需要分析的推文：

{tweets_text}

请以中文形式生成一份专业、有深度的分析报告，使用清晰的结构，突出关键发现和洞察。报告长度不超过1000字。不要逐条分析每条推文，而是提供整体性的分析和见解。
"""
        
        return prompt
    
    def _call_api(self, prompt: str) -> str:
        """
        调用DeepSeek API
        
        Args:
            prompt: 分析提示
            
        Returns:
            str: API响应内容
        """
        if not self.api_key:
            self.logger.warning("DeepSeek API密钥未配置，使用模拟响应")
            return self._mock_response(prompt)
            
        try:
            # DeepSeek API端点
            api_url = "https://api.deepseek.com/v1/chat/completions"
            
            # 请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 请求体
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一位专业的AI技术分析师，擅长分析技术趋势和研究动态。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # 发送请求
            response = requests.post(api_url, headers=headers, json=data)
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                self.logger.error(f"DeepSeek API错误: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"调用DeepSeek API时出错: {e}")
            return None
    
    def _mock_response(self, prompt: str) -> str:
        """
        生成模拟响应（当API密钥未配置时）
        
        Args:
            prompt: 分析提示
            
        Returns:
            str: 模拟的分析报告
        """
        return """# AI领域最新动态分析报告

## 总体概述
当前AI领域正处于快速发展阶段，大型语言模型(LLM)技术持续演进，多模态AI系统成为热点，AI安全和治理问题受到广泛关注。专家们普遍关注模型效率优化、推理能力提升和实际应用落地问题。

## 技术趋势
1. **模型架构优化**：研究人员正致力于提高Transformer架构效率，探索注意力机制替代方案
2. **小型高效模型**：小参数量但高性能的模型成为研究热点，适合边缘设备部署
3. **多模态融合**：视觉-语言模型取得突破，能够更自然地理解和生成跨模态内容
4. **推理能力增强**：提升模型的逻辑推理和因果推断能力是当前重点方向
5. **自监督学习进展**：减少对标记数据依赖的自监督方法不断取得进展

## 研究方向
- **知识整合**：将结构化知识与神经网络模型有效结合
- **稀疏激活**：探索只激活部分网络的模型训练方法，提高计算效率
- **长序列建模**：提高模型处理长文本和长对话的能力
- **对齐与安全**：确保AI系统行为符合人类意图和价值观
- **跨领域迁移**：研究模型在不同任务和领域间的知识迁移能力

## 产业影响
这些技术进步将促进AI在医疗诊断、科学研究、内容创作等领域的应用深化。企业正加速采用AI技术提升生产力，同时关注模型部署成本和效率问题。开源模型生态系统蓬勃发展，降低了AI应用门槛，促进技术民主化。

## 专家观点
领域专家普遍认为，虽然大型模型取得了显著进展，但真正的通用人工智能仍面临挑战。多位专家强调了提高模型解释性和可靠性的重要性，以及负责任发展AI的必要性。对于AI治理，专家们呼吁建立平衡创新与安全的监管框架。

---

这些发展表明AI领域正在从纯粹的模型规模竞赛转向更注重效率、能力和责任的方向，未来研究将更加关注如何构建既强大又可靠、既先进又负责任的AI系统。"""