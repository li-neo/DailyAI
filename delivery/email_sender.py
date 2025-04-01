#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
邮件发送模块

负责将AI日报以邮件形式发送给订阅者。
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List
from models.tweet import Tweet
from models.report import Report
from utils.logger import get_logger

class EmailSender:
    """
    邮件发送器
    
    负责构建和发送AI日报邮件。
    """
    
    def __init__(self, smtp_config, email_config):
        """
        初始化邮件发送器
        
        Args:
            smtp_config: SMTP服务器配置
            email_config: 邮件发送配置
        """
        self.smtp_config = smtp_config
        self.email_config = email_config
        self.logger = get_logger(__name__)
    
    def send_daily_report(self, tweets: List[Tweet], analysis: str):
        """
        发送每日AI报告
        
        Args:
            tweets: 排序后的推文列表
            analysis: DeepSeek分析报告
            
        Returns:
            bool: 是否发送成功
        """
        if not tweets:
            self.logger.warning("没有推文数据，取消发送邮件")
            return False
            
        try:
            # 创建报告对象
            report = Report(
                date=datetime.now(),
                title=f"AI日报 - {datetime.now().strftime('%Y年%m月%d日')}",
                tweets=tweets,
                analysis=analysis,
                summary=self._generate_summary(tweets),
                trends=self._extract_trends(analysis)
            )
            
            # 生成邮件HTML内容
            html_content = report.format_email_html()
            
            # 发送邮件
            subject = self.email_config.get('subject_template', 'AI日报 - {date}').format(
                date=datetime.now().strftime('%Y年%m月%d日')
            )
            
            recipients = self.email_config.get('recipients', [])
            if not recipients:
                self.logger.warning("没有收件人，取消发送邮件")
                return False
                
            return self._send_email(subject, html_content, recipients)
            
        except Exception as e:
            self.logger.error(f"发送邮件时出错: {e}")
            return False
    
    def _send_email(self, subject, html_content, recipients):
        """
        发送HTML格式邮件
        
        Args:
            subject: 邮件主题
            html_content: HTML邮件内容
            recipients: 收件人列表
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config.get('sender', 'AI日报 <noreply@example.com>')
            msg['To'] = ', '.join(recipients)
            
            # 添加HTML内容
            msg.attach(MIMEText(html_content, 'html'))
            
            # 设置超时时间
            timeout = self.smtp_config.get('timeout', 30)  # 默认30秒超时
            
            # 连接到SMTP服务器
            server = smtplib.SMTP(
                self.smtp_config.get('server', 'smtp.gmail.com'),
                self.smtp_config.get('port', 587),
                timeout=timeout
            )
            
            # 设置更详细的日志
            if self.smtp_config.get('debug', False):
                server.set_debuglevel(1)
            
            # 尝试EHLO命令
            server.ehlo()
            
            # 检查服务器是否支持STARTTLS
            if self.smtp_config.get('use_tls', True):
                if server.has_extn('STARTTLS'):
                    server.starttls()
                    server.ehlo()  # 需要在STARTTLS后重新识别
                else:
                    self.logger.warning("SMTP服务器不支持STARTTLS，尝试明文传输")
            
            # 登录
            if self.smtp_config.get('username') and self.smtp_config.get('password'):
                server.login(
                    self.smtp_config.get('username', ''),
                    self.smtp_config.get('password', '')
                )
                self.logger.debug("SMTP登录成功")
            else:
                self.logger.warning("未提供SMTP用户名或密码，尝试不认证发送")
            
            # 发送邮件
            sender = self.smtp_config.get('username', '') or self.smtp_config.get('sender', '').split('<')[-1].strip('>')
            server.sendmail(
                sender,
                recipients,
                msg.as_string()
            )
            self.logger.debug(f"邮件已发送给: {recipients}")
            
            # 关闭连接
            server.quit()
            
            self.logger.info(f"成功发送邮件给 {len(recipients)} 位收件人")
            return True
            
        except smtplib.SMTPConnectError as e:
            self.logger.error(f"连接SMTP服务器失败: {e}")
            return False
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP认证失败: {e}")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP错误: {e}")
            return False
        except TimeoutError as e:
            self.logger.error(f"连接SMTP服务器超时: {e}")
            return False
        except ConnectionRefusedError as e:
            self.logger.error(f"连接被拒绝: {e}")
            return False
        except Exception as e:
            self.logger.error(f"发送邮件失败: {e}")
            return False
    
    def _generate_summary(self, tweets: List[Tweet]) -> str:
        """
        生成简短摘要
        
        Args:
            tweets: 推文列表
            
        Returns:
            str: 摘要文本
        """
        author_count = len(set(t.author for t in tweets))
        topics = self._extract_topics(tweets)
        
        summary = f"今日AI日报收集了来自 {author_count} 位AI领域专家的 {len(tweets)} 条高质量推文，"
        
        if topics:
            summary += f"主要涉及 {', '.join(topics[:3])} 等主题。"
        else:
            summary += "涵盖了AI领域的最新进展和热点话题。"
            
        return summary
    
    def _extract_topics(self, tweets: List[Tweet]) -> List[str]:
        """
        从推文中提取主题关键词
        
        Args:
            tweets: 推文列表
            
        Returns:
            list: 主题关键词列表
        """
        # 这里可以实现更复杂的主题提取算法
        # 简单实现：使用预定义的关键词
        topics = []
        keywords = {
            "大模型": ["LLM", "large language model", "GPT", "大模型"],
            "机器学习": ["machine learning", "ML", "机器学习"],
            "神经网络": ["neural network", "神经网络", "neural net"],
            "强化学习": ["reinforcement learning", "RL", "强化学习"],
            "计算机视觉": ["computer vision", "CV", "计算机视觉", "视觉"],
            "自然语言处理": ["NLP", "natural language", "自然语言"],
            "多模态": ["multimodal", "多模态"],
            "生成式AI": ["generative AI", "生成式", "generative"],
            "AI安全": ["AI safety", "安全", "safety", "alignment"],
            "AI伦理": ["ethics", "伦理", "responsible AI"],
            "AI监管": ["regulation", "监管", "governance"]
        }
        
        # 统计关键词出现频率
        topic_counts = {topic: 0 for topic in keywords}
        for tweet in tweets:
            content_lower = tweet.content.lower()
            for topic, topic_keywords in keywords.items():
                for keyword in topic_keywords:
                    if keyword.lower() in content_lower:
                        topic_counts[topic] += 1
                        break
        
        # 按频率排序，返回出现的主题
        return [topic for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True) if count > 0]
    
    def _extract_trends(self, analysis: str) -> List[str]:
        """
        从分析报告中提取趋势要点
        
        Args:
            analysis: 分析报告文本
            
        Returns:
            list: 趋势要点列表
        """
        trends = []
        
        # 简单实现：查找特定标题后的要点
        try:
            # 查找技术趋势部分
            if "## 技术趋势" in analysis:
                trend_section = analysis.split("## 技术趋势")[1].split("##")[0]
                # 提取数字编号的要点
                import re
                trend_items = re.findall(r'\d+\.\s+\*\*(.+?)\*\*：(.+?)(?=$|\n\d+\.)', trend_section, re.DOTALL)
                if trend_items:
                    for title, desc in trend_items:
                        trends.append(f"{title}：{desc.strip()}")
                else:
                    # 尝试提取其他格式的要点
                    trend_items = re.findall(r'[*-]\s+(.+?)(?=$|\n[*-])', trend_section, re.DOTALL)
                    trends.extend([item.strip() for item in trend_items if item.strip()])
        except Exception:
            # 失败时返回空列表
            pass
            
        return trends