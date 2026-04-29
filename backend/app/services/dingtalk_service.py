"""
钉钉推送服务 - 发送预警消息到钉钉群
"""
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.core.logger import logger


class DingTalkService:
    """钉钉推送服务"""
    
    def __init__(self):
        self.webhook_url = settings.DINGTALK_WEBHOOK_URL
        self.secret = settings.DINGTALK_SECRET
        self.enabled = settings.DINGTALK_ENABLED
        self.timeout = 10
    
    def _sign(self) -> str:
        """计算签名(如果配置了secret)"""
        if not self.secret:
            return ""
        
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return f"&timestamp={timestamp}&sign={sign}"
    
    def _get_url(self) -> str:
        """获取带签名的完整URL"""
        return self.webhook_url + self._sign()
    
    def send_text(self, content: str, at_all: bool = False, at_mobiles: Optional[List[str]] = None) -> bool:
        """
        发送纯文本消息
        
        Args:
            content: 消息内容
            at_all: 是否@所有人
            at_mobiles: 需要@的手机号列表
        
        Returns:
            是否发送成功
        """
        if not self.enabled or not self.webhook_url:
            logger.debug("钉钉推送未启用或未配置Webhook")
            return False
        
        data = {
            "msgtype": "text",
            "text": {"content": content},
            "at": {
                "isAtAll": at_all,
                "atMobiles": at_mobiles or [],
            }
        }
        
        return self._send(data)
    
    def send_markdown(self, title: str, text: str, at_all: bool = False, at_mobiles: Optional[List[str]] = None) -> bool:
        """
        发送Markdown消息
        
        Args:
            title: 标题(显示在通知栏)
            text: Markdown格式内容
            at_all: 是否@所有人
            at_mobiles: 需要@的手机号列表
        
        Returns:
            是否发送成功
        """
        if not self.enabled or not self.webhook_url:
            logger.debug("钉钉推送未启用或未配置Webhook")
            return False
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text,
            },
            "at": {
                "isAtAll": at_all,
                "atMobiles": at_mobiles or [],
            }
        }
        
        return self._send(data)
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        发送预警消息
        
        Args:
            alert: 预警信息字典,包含level, title, message, product_name等
        
        Returns:
            是否发送成功
        """
        level = alert.get("level", "info")
        level_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(level, "⚪")
        level_text = {"critical": "严重", "warning": "警告", "info": "提示"}.get(level, "通知")
        
        title = f"{level_emoji} FOF预警 - {alert.get('title', '未知')}"
        
        lines = [
            f"### {level_emoji} {level_text}: {alert.get('title', '')}",
            "",
            f"**产品**: {alert.get('product_name', '-')}",
            f"**管理人**: {alert.get('manager_name', '-')}",
            f"**详情**: {alert.get('message', '-')}",
            f"**日期**: {alert.get('date', '-')}",
            "",
            f"> 类型: {alert.get('type', '-')} | 阈值: {alert.get('threshold', '-')}",
        ]
        
        return self.send_markdown(title, "\n".join(lines), at_all=(level == "critical"))
    
    def send_alerts_summary(self, alerts: List[Dict[str, Any]]) -> bool:
        """
        发送预警汇总消息
        
        Args:
            alerts: 预警列表
        
        Returns:
            是否发送成功
        """
        if not alerts:
            return True
        
        critical = [a for a in alerts if a.get("level") == "critical"]
        warning = [a for a in alerts if a.get("level") == "warning"]
        
        title = f"📊 FOF预警汇总 ({len(alerts)}条)"
        
        lines = [
            f"### 📊 FOF预警汇总",
            "",
            f"- 🔴 严重: **{len(critical)}** 条",
            f"- 🟡 警告: **{len(warning)}** 条",
            f"- 总计: **{len(alerts)}** 条",
            "",
        ]
        
        # 列出严重预警
        if critical:
            lines.append("#### 严重预警:")
            for a in critical[:5]:
                lines.append(f"- {a.get('product_name', '')} - {a.get('title', '')}")
            if len(critical) > 5:
                lines.append(f"- ...还有 {len(critical) - 5} 条")
            lines.append("")
        
        # 列出部分警告
        if warning:
            lines.append("#### 警告预警 (前5条):")
            for a in warning[:5]:
                lines.append(f"- {a.get('product_name', '')} - {a.get('title', '')}")
            if len(warning) > 5:
                lines.append(f"- ...还有 {len(warning) - 5} 条")
        
        return self.send_markdown(title, "\n".join(lines), at_all=bool(critical))
    
    def _send(self, data: dict) -> bool:
        """发送消息到钉钉"""
        try:
            url = self._get_url()
            resp = requests.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            result = resp.json()
            
            if result.get("errcode") == 0:
                logger.info("钉钉消息发送成功")
                return True
            else:
                logger.error(f"钉钉消息发送失败: {result.get('errmsg', '未知错误')}")
                return False
        except Exception as e:
            logger.error(f"钉钉消息发送异常: {e}")
            return False


# 全局单例
dingtalk_service = DingTalkService()
