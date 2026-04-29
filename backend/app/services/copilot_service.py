"""
AI Copilot context builder and response orchestration.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import json
import time

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.ai_report import AIReport
from app.models.document import Document
from app.models.fund_performance import FundExtendedInfo, FundPerformance
from app.models.manager import Manager
from app.models.nav import NavData
from app.models.news_article import NewsArticle
from app.models.portfolio import Portfolio, PortfolioComponent, PortfolioNav
from app.models.product import Product
from app.models.project import Project
from app.models.task import Task
from app.services.alert_service import AlertService
from app.services.llm_service import llm_service


MODULE_PROFILES: Dict[str, Dict[str, Any]] = {
    "dashboard": {
        "name": "总览",
        "role": "FOF投研运营总览助手",
        "questions": ["当前平台最需要优先关注什么？", "管理人和产品结构是否均衡？", "今天应推进哪些投研动作？"],
        "planning": ["识别资产、管理人、项目、任务四类经营信号", "拆解优先级与责任动作", "给出可执行的下一步清单"],
    },
    "managers": {
        "name": "管理人管理",
        "role": "管理人研究与准入助手",
        "questions": ["哪些管理人值得进入重点跟踪？", "当前跟踪池流转是否合理？", "需要补充哪些尽调信息？"],
        "planning": ["先看池分类与策略覆盖", "再看评级、合规、舆情和产品数量", "最后形成准入、观察或淘汰建议"],
    },
    "products": {
        "name": "产品管理",
        "role": "私募产品分析助手",
        "questions": ["哪些产品近期表现最好？", "产品风险暴露集中在哪里？", "哪些产品需要补充净值或分析？"],
        "planning": ["核对状态、策略、净值更新完整度", "比较收益、回撤、波动和夏普", "输出产品跟踪和配置建议"],
    },
    "product-detail": {
        "name": "产品详情",
        "role": "单产品深度研究助手",
        "questions": ["这个产品的核心风险是什么？", "是否适合进入组合观察池？", "后续跟踪要看哪些指标？"],
        "planning": ["先解释产品基础信息", "再定位业绩与风控指标", "形成跟踪问题和验证路径"],
    },
    "portfolios": {
        "name": "组合管理",
        "role": "FOF组合配置助手",
        "questions": ["当前组合配置有什么隐患？", "哪些组合收益风险更优？", "是否需要调仓或再平衡？"],
        "planning": ["检查组合状态、成分和净值", "比较收益、回撤与权重集中度", "给出组合层面的再平衡方向"],
    },
    "projects": {
        "name": "一级项目",
        "role": "一级项目投研推进助手",
        "questions": ["哪些项目推进风险最高？", "投决前还缺哪些材料？", "项目管线是否健康？"],
        "planning": ["按阶段拆解项目管线", "识别尽调、投决、投后关键节点", "给出推进节奏和风险提示"],
    },
    "ranking": {
        "name": "市场数据",
        "role": "市场排行分析助手",
        "questions": ["市场排名中有哪些异常信号？", "哪些策略近期占优？", "可以挖掘哪些候选产品？"],
        "planning": ["比较收益排行和风险排行", "关注策略分层与极端值", "形成候选池筛选逻辑"],
    },
    "analysis": {
        "name": "产品分析",
        "role": "产品量化分析助手",
        "questions": ["当前分析数据说明什么？", "哪些产品需要重新分析？", "如何解释收益和回撤来源？"],
        "planning": ["先看数据覆盖率", "再读收益风险指标", "输出复核和研究动作"],
    },
    "attribution": {
        "name": "因子归因",
        "role": "因子归因研究助手",
        "questions": ["主要收益来源是什么？", "风格暴露是否稳定？", "归因结果如何用于调仓？"],
        "planning": ["读取归因覆盖情况", "判断风格暴露与绩效一致性", "给出组合应用建议"],
    },
    "alerts": {
        "name": "异常预警",
        "role": "风险预警处置助手",
        "questions": ["当前最高优先级预警是什么？", "哪些预警需要马上处置？", "预警规则是否需要调整？"],
        "planning": ["按严重程度排序", "追溯触发原因和影响范围", "输出处置动作与复核标准"],
    },
    "ai-reports": {
        "name": "AI智能报告",
        "role": "投研报告助手",
        "questions": ["哪些报告需要更新？", "报告结论是否足够可执行？", "怎么组织一份投委会材料？"],
        "planning": ["查看报告类型、状态和更新时间", "提炼结论、风险和行动", "生成汇报结构"],
    },
    "documents": {
        "name": "尽调资料",
        "role": "尽调资料整理助手",
        "questions": ["资料库还缺哪些关键文件？", "哪些资料需要关联到项目或管理人？", "如何形成尽调清单？"],
        "planning": ["按资料类型和关联对象检查完整度", "识别缺口和重复项", "输出补充清单"],
    },
    "tasks": {
        "name": "待办任务",
        "role": "投研任务规划助手",
        "questions": ["今天优先处理哪些任务？", "哪些任务有逾期风险？", "任务分配是否合理？"],
        "planning": ["按状态、优先级、截止日排序", "识别依赖和逾期风险", "给出今日执行计划"],
    },
}

PATH_MODULE_RULES = [
    ("product-detail", lambda p: p.startswith("/products/") and p != "/products"),
    ("managers", lambda p: p.startswith("/managers")),
    ("products", lambda p: p.startswith("/products")),
    ("portfolios", lambda p: p.startswith("/portfolios")),
    ("projects", lambda p: p.startswith("/projects")),
    ("ranking", lambda p: p.startswith("/ranking")),
    ("analysis", lambda p: p.startswith("/analysis")),
    ("attribution", lambda p: p.startswith("/attribution")),
    ("alerts", lambda p: p.startswith("/alerts")),
    ("ai-reports", lambda p: p.startswith("/ai-reports")),
    ("documents", lambda p: p.startswith("/documents")),
    ("tasks", lambda p: p.startswith("/tasks")),
    ("dashboard", lambda p: p in ("", "/")),
]

GLOBAL_CACHE_TTL_SECONDS = 300
_GLOBAL_COPILOT_CACHE: Dict[str, Any] = {}


def _read_global_cache(key: str) -> Optional[Any]:
    record = _GLOBAL_COPILOT_CACHE.get(key)
    if not record:
        return None
    if time.time() - record["ts"] > GLOBAL_CACHE_TTL_SECONDS:
        _GLOBAL_COPILOT_CACHE.pop(key, None)
        return None
    return record["value"]


def _write_global_cache(key: str, value: Any) -> Any:
    _GLOBAL_COPILOT_CACHE[key] = {"ts": time.time(), "value": value}
    return value


def _safe_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _rows_to_dict(rows: List[Any], empty_key: str = "未分类") -> Dict[str, int]:
    data: Dict[str, int] = {}
    for key, count in rows:
        normalized = _safe_value(key) or empty_key
        data[str(normalized)] = int(count or 0)
    return data


def _as_float(value: Any) -> Optional[float]:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _avg(values: List[Optional[float]]) -> Optional[float]:
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 6)


def _pct(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    return f"{value * 100:.2f}%"


def _parse_series_date(value: Any) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


class CopilotService:
    """Builds module data context and sends chat requests to the LLM."""

    def __init__(self, db: Session):
        self.db = db
        self._top_products_cache: Optional[List[Dict[str, Any]]] = None
        self._strategy_performance_cache: Optional[List[Dict[str, Any]]] = None
        self._manager_leaders_cache: Optional[List[Dict[str, Any]]] = None

    def resolve_module(self, path: Optional[str], module_key: Optional[str] = None) -> str:
        if module_key in MODULE_PROFILES:
            return str(module_key)

        normalized = (path or "/").split("?")[0]
        for key, matcher in PATH_MODULE_RULES:
            if matcher(normalized):
                return key
        return "dashboard"

    def get_context(self, path: Optional[str] = None, module_key: Optional[str] = None) -> Dict[str, Any]:
        key = self.resolve_module(path, module_key)
        profile = MODULE_PROFILES[key]
        data = self._build_data(key, path or "/")
        cards = self._build_cards(data)

        return {
            "module_key": key,
            "module_name": profile["name"],
            "role": profile["role"],
            "questions": profile["questions"],
            "planning": profile["planning"],
            "core_data": data,
            "cards": cards,
            "disclaimer": "AI 生成内容仅供研究参考，可能存在偏差或错误，不构成任何投资建议。",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }

    def chat(
        self,
        question: str,
        path: Optional[str] = None,
        module_key: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        context = self.get_context(path=path, module_key=module_key)
        profile = MODULE_PROFILES[context["module_key"]]
        global_context = self._global_research_context(context["module_key"])
        related_context = self._related_context_from_question(question)
        context_text = self._compact_json(context["core_data"], 14000)
        global_text = self._compact_json(global_context, 12000)
        related_text = self._compact_json(related_context, 10000)
        attachment_text = self._format_attachments(attachments or [])

        system_prompt = f"""你是{profile['role']}，服务于FOF管理平台的专业AI Copilot。
你的读者是投资经理、投研负责人或投委会成员，不是程序员。请用投资经理之间沟通的方式回答。
你必须基于页面自动带入的模块核心数据回答，若数据不足，要用业务语言说明缺口并给出下一步验证路径。
当前页面只是入口，不代表只能使用当前表格数据。你可以同时使用：
- 当前模块数据；
- 子页面/详情页可获得的产品、管理人、组合穿透数据；
- 全项目投研快照，用于横向比较和组合判断。

回答风格：
1. 像投研会前的口径整理：先一句话判断，再讲核心依据、取舍逻辑和下一步动作；
2. 语言友好、稳健、直接，不使用“字段为空、JSON、接口、raw_data、return_1y、drawdown_1y”等技术表达；
3. 少写长篇定义，多给可执行的投资观察、组合构建思路、风险边界和复核清单；
4. 如需列表，优先使用“观点/依据/组合建议/关注事项”的自然结构，表格要简洁；
5. 不要把高收益产品直接等同于好产品，要同时看回撤、样本代表性、策略分散和业绩可持续性；
6. 如果提出5只产品组合，要称为“候选组合”或“模拟组合思路”，避免绝对化推荐，并给出建议权重区间或角色分工；
7. 结论必须前后一致：如果某产品因回撤过高被排除，就不要再放入组合；
8. 最终5只组合必须满足你自己设定的筛选条件；高波动或超阈值产品只能放在“观察/备选名单”，不要混入正式5只；
9. 面对投资经理时默认控制篇幅，优先说重点，避免过长铺陈；
10. 如果“问题相关对象穿透数据”里已经有产品/管理人详情，不要再要求用户自己去详情页确认同一批指标，应直接基于这些详情数据分析；
11. 涉及投资判断时必须强调仅供研究参考，不构成投资建议；
12. 不编造页面数据之外的事实，不确定时说明假设。
当前模块：{context['module_name']}
专业引导规划：{'；'.join(profile['planning'])}
模块核心数据：
{context_text}

全项目投研快照：
{global_text}

问题相关对象穿透数据：
{related_text}
{attachment_text}
"""

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for item in (history or [])[-8:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content[:3000]})
        messages.append({"role": "user", "content": question})

        requested_provider = provider or llm_service.default_provider
        provider_used = requested_provider
        answer = llm_service.chat_completion(
            messages=messages,
            temperature=0.35,
            max_tokens=1600,
            provider=requested_provider,
        )

        if not answer and requested_provider != llm_service.fallback_provider:
            logger.warning(
                f"Copilot模型通道不可用，自动切换兜底通道: "
                f"from={requested_provider}, to={llm_service.fallback_provider}"
            )
            provider_used = llm_service.fallback_provider
            answer = llm_service.chat_completion(
                messages=messages,
                temperature=0.35,
                max_tokens=1600,
                provider=llm_service.fallback_provider,
            )

        if not answer:
            answer = self._fallback_answer(context, question, global_context, related_context)

        return {
            "answer": answer,
            "module_key": context["module_key"],
            "module_name": context["module_name"],
            "used_questions": context["questions"],
            "attachments": attachments or [],
            "provider": provider_used,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }

    def chat_stream(
        self,
        question: str,
        path: Optional[str] = None,
        module_key: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[str] = None,
    ):
        """流式输出版本的chat方法，返回生成器用于SSE"""
        import json
        
        context = self.get_context(path=path, module_key=module_key)
        profile = MODULE_PROFILES[context["module_key"]]
        global_context = self._global_research_context(context["module_key"])
        related_context = self._related_context_from_question(question)
        context_text = self._compact_json(context["core_data"], 14000)
        global_text = self._compact_json(global_context, 12000)
        related_text = self._compact_json(related_context, 10000)
        attachment_text = self._format_attachments(attachments or [])

        system_prompt = f"""你是{profile['role']}，服务于FOF管理平台的专业AI Copilot。
你的读者是投资经理、投研负责人或投委会成员，不是程序员。请用投资经理之间沟通的方式回答。
你必须基于页面自动带入的模块核心数据回答，若数据不足，要用业务语言说明缺口并给出下一步验证路径。
当前页面只是入口，不代表只能使用当前表格数据。你可以同时使用：
- 当前模块数据；
- 子页面/详情页可获得的产品、管理人、组合穿透数据；
- 全项目投研快照，用于横向比较和组合判断。

回答风格：
1. 像投研会前的口径整理：先一句话判断，再讲核心依据、取舍逻辑和下一步动作；
2. 语言友好、稳健、直接，不使用"字段为空、JSON、接口、raw_data、return_1y、drawdown_1y"等技术表达；
3. 少写长篇定义，多给可执行的投资观察、组合构建思路、风险边界和复核清单；
4. 如需列表，优先使用"观点/依据/组合建议/关注事项"的自然结构，表格要简洁；
5. 不要把高收益产品直接等同于好产品，要同时看回撤、样本代表性、策略分散和业绩可持续性；
6. 如果提出5只产品组合，要称为"候选组合"或"模拟组合思路"，避免绝对化推荐，并给出建议权重区间或角色分工；
7. 结论必须前后一致：如果某产品因回撤过高被排除，就不要再放入组合；
8. 最终5只组合必须满足你自己设定的筛选条件；高波动或超阈值产品只能放在"观察/备选名单"，不要混入正式5只；
9. 面对投资经理时默认控制篇幅，优先说重点，避免过长铺陈；
10. 如果"问题相关对象穿透数据"里已经有产品/管理人详情，不要再要求用户自己去详情页确认同一批指标，应直接基于这些详情数据分析；
11. 涉及投资判断时必须强调仅供研究参考，不构成投资建议；
12. 不编造页面数据之外的事实，不确定时说明假设。
当前模块：{context['module_name']}
专业引导规划：{'；'.join(profile['planning'])}
模块核心数据：
{context_text}

全项目投研快照：
{global_text}

问题相关对象穿透数据：
{related_text}
{attachment_text}
"""

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for item in (history or [])[-8:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content[:3000]})
        messages.append({"role": "user", "content": question})

        requested_provider = provider or llm_service.default_provider
        provider_used = requested_provider
        
        # 调用流式API
        response = llm_service.chat_completion(
            messages=messages,
            temperature=0.35,
            max_tokens=1600,
            stream=True,
            provider=requested_provider,
        )

        # 如果主通道失败，尝试兜底通道
        if not response and requested_provider != llm_service.fallback_provider:
            logger.warning(
                f"Copilot模型通道不可用，自动切换兜底通道: "
                f"from={requested_provider}, to={llm_service.fallback_provider}"
            )
            provider_used = llm_service.fallback_provider
            response = llm_service.chat_completion(
                messages=messages,
                temperature=0.35,
                max_tokens=1600,
                stream=True,
                provider=llm_service.fallback_provider,
            )

        # 如果仍然失败，返回兜底答案
        if not response:
            fallback_answer = self._fallback_answer(context, question, global_context, related_context)
            yield f"data: {json.dumps({'content': fallback_answer, 'done': True}, ensure_ascii=False)}\n\n"
            return

        # 流式输出
        try:
            for line in response.iter_lines():
                if not line:
                    continue
                
                line_text = line.decode('utf-8', errors='replace').strip()
                if not line_text.startswith('data:'):
                    continue
                
                data = line_text[5:].strip()
                if not data or data == '[DONE]':
                    # 发送完成标记
                    yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                    break
                
                try:
                    chunk = json.loads(data)
                    choice = (chunk.get('choices') or [{}])[0]
                    delta = choice.get('delta') or {}
                    content = delta.get('content')
                    
                    if content:
                        # 发送内容片段
                        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                    
                    # 检查是否完成
                    if choice.get('finish_reason'):
                        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                        break
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.error(f"流式输出异常: {e}")
            yield f"data: {json.dumps({'error': str(e), 'done': True}, ensure_ascii=False)}\n\n"

    def _format_attachments(self, attachments: List[Dict[str, Any]]) -> str:
        if not attachments:
            return ""

        blocks: List[str] = ["\n用户本轮上传/粘贴的附件材料："]
        for idx, item in enumerate(attachments[:5], start=1):
            name = item.get("filename") or f"附件{idx}"
            status = item.get("extract_status") or "unknown"
            kind = item.get("kind") or "file"
            blocks.append(f"\n附件{idx}：{name}（{kind}，解析状态：{status}）")
            if item.get("text"):
                blocks.append(str(item["text"])[:6000])
            elif item.get("summary"):
                blocks.append(str(item["summary"])[:1000])
            else:
                blocks.append("未提取到可用于分析的文本内容。")

        blocks.append("\n请把附件内容与当前模块数据一起使用；如果图片无法直接识别，请明确请用户补充图片中的关键文字或数据。")
        return "\n".join(blocks)

    def _compact_json(self, data: Any, limit: int) -> str:
        text = json.dumps(data, ensure_ascii=False, default=_safe_value, indent=2)
        if len(text) <= limit:
            return text
        return text[:limit] + "\n...[上下文已压缩截断]"

    def _fallback_answer(
        self,
        context: Dict[str, Any],
        question: str,
        global_context: Optional[Dict[str, Any]] = None,
        related_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        matched_products = (related_context or {}).get("matched_products") or []
        if matched_products:
            product = matched_products[0]
            strategy = product.get("strategy")
            peers = (global_context or {}).get("strategy_recent_performance") or []
            peer = next((item for item in peers if item.get("strategy") == strategy), None)
            perf = product.get("performance") or {}
            nav = product.get("nav") or {}
            lines = [
                f"我已经穿透到【{product.get('name')}】的产品详情数据，不需要再手工去详情页确认同一批指标。",
                "",
                "**一句话判断：**",
                f"{product.get('name')}属于{strategy or '未分类'}，净值样本从{nav.get('first_date') or '-'}到{nav.get('latest_date') or '-'}，共有{nav.get('record_count') or 0}条记录。近一年收益{perf.get('return_1y') or '-'}、近一年最大回撤{perf.get('max_drawdown_1y') or '-'}、夏普{perf.get('sharpe_ratio_1y') or '-'}。",
            ]
            if peer:
                lines.extend(
                    [
                        "",
                        "**同类对比：**",
                        f"{strategy}当前可比样本{peer.get('available_1y_count')}只，策略近一年平均收益{peer.get('avg_return_1y')}、平均最大回撤{peer.get('avg_max_drawdown_1y')}、平均夏普{peer.get('avg_sharpe_ratio_1y')}。",
                        "因此可以直接把它放在同类策略里看收益弹性、回撤控制和风险调整后表现，而不是只看当前概览表。",
                    ]
                )
            lines.extend(
                [
                    "",
                    "**下一步建议：**",
                    "如果用于FOF候选池，建议继续看月度收益分布、极端回撤发生时间、与现有组合的相关性，以及管理人旗下其他产品是否表现一致。以上仅供研究参考，不构成投资建议。",
                ]
            )
            return "\n".join(lines)

        cards = context.get("cards") or []
        card_lines = "\n".join([f"- {c['label']}: {c['value']}" for c in cards[:6]])
        planning = "；".join(context.get("planning") or [])
        return (
            f"我已读取【{context['module_name']}】模块数据，但当前模型服务未返回有效内容。\n\n"
            f"针对你的问题“{question}”，可先按这个路径推进：{planning}。\n\n"
            f"当前关键数据：\n{card_lines}\n\n"
            "建议先核对异常值、数据缺口和最近更新日期，再形成正式研究判断。以上仅供研究参考，不构成投资建议。"
        )

    def _build_cards(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        cards: List[Dict[str, str]] = []
        summary = data.get("summary") or {}
        for key, value in summary.items():
            label = str(key).replace("_", " ")
            cards.append({"label": label, "value": str(_safe_value(value))})
        return cards

    def _global_research_context(self, current_module: str) -> Dict[str, Any]:
        """Small cross-project snapshot available to every Copilot entry."""
        strategy_rows = self._strategy_recent_performance()[:8]
        top_products = self._top_products_from_raw()[:12]
        return {
            "scope": "全项目投研快照",
            "current_module": current_module,
            "summary": {
                "管理人总数": self.db.query(Manager).filter(Manager.is_deleted == False).count(),
                "产品总数": self.db.query(Product).count(),
                "业绩样本": self.db.query(FundPerformance).count(),
                "组合总数": self.db.query(Portfolio).filter(Portfolio.is_deleted == False).count(),
                "净值记录数": self.db.query(NavData).count(),
            },
            "strategy_recent_performance": strategy_rows,
            "top_products_by_1y": top_products,
            "manager_performance_leaders": self._manager_performance_leaders()[:10],
            "manager_pool_distribution": _rows_to_dict(
                self.db.query(Manager.pool_category, func.count(Manager.id))
                .filter(Manager.is_deleted == False)
                .group_by(Manager.pool_category)
                .all()
            ),
        }

    def _related_context_from_question(self, question: str) -> Dict[str, Any]:
        """Pull detail-page data for products/managers explicitly mentioned by the user."""
        if not question:
            return {"matched_products": [], "matched_managers": []}

        products = self._match_products(question)
        managers = self._match_managers(question)

        return {
            "matched_products": [self._product_snapshot(product) for product in products[:5]],
            "matched_managers": [self._manager_snapshot(manager) for manager in managers[:5]],
        }

    def _match_products(self, question: str) -> List[Product]:
        candidates = self.db.query(Product).all()
        scored: List[tuple[int, Product]] = []
        normalized_question = question.lower()
        for product in candidates:
            name = product.product_name or ""
            short_tokens = [token for token in name.replace("私募证券投资基金", " ").replace("私募基金", " ").replace("集合资金信托计划", " ").split() if token]
            score = 0
            if name and name in question:
                score += 100
            if product.product_code and product.product_code.lower() in normalized_question:
                score += 80
            for token in short_tokens:
                if len(token) >= 2 and token in question:
                    score += min(len(token), 20)
            # Chinese product names are often typed partially; count common characters for longer mentions.
            common_chars = len(set(name) & set(question))
            if common_chars >= 4:
                score += common_chars
            if score >= 8:
                scored.append((score, product))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [product for _, product in scored]

    def _match_managers(self, question: str) -> List[Manager]:
        candidates = self.db.query(Manager).filter(Manager.is_deleted == False).all()
        scored: List[tuple[int, Manager]] = []
        normalized_question = question.lower()
        for manager in candidates:
            name = manager.manager_name or ""
            score = 0
            if name and name in question:
                score += 100
            if manager.short_name and manager.short_name in question:
                score += 80
            if manager.manager_code and manager.manager_code.lower() in normalized_question:
                score += 60
            common_chars = len(set(name) & set(question))
            if common_chars >= 3:
                score += common_chars
            if score >= 6:
                scored.append((score, manager))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [manager for _, manager in scored]

    def _product_snapshot(self, product: Product) -> Dict[str, Any]:
        perf = (
            self.db.query(FundPerformance)
            .filter(FundPerformance.product_id == product.id)
            .order_by(desc(FundPerformance.update_date))
            .first()
        )
        latest_nav = (
            self.db.query(NavData)
            .filter(NavData.product_id == product.id)
            .order_by(desc(NavData.nav_date))
            .first()
        )
        first_nav_date = self.db.query(func.min(NavData.nav_date)).filter(NavData.product_id == product.id).scalar()
        nav_count = self.db.query(func.count(NavData.id)).filter(NavData.product_id == product.id).scalar()
        metrics = self._performance_metrics(perf) if perf else {}
        return {
            "id": product.id,
            "name": product.product_name,
            "manager": product.manager.manager_name if product.manager else None,
            "strategy": product.strategy_type,
            "status": product.status,
            "is_invested": product.is_invested,
            "nav": {
                "first_date": _safe_value(first_nav_date),
                "latest_date": _safe_value(latest_nav.nav_date) if latest_nav else None,
                "latest_unit_nav": _safe_value(latest_nav.unit_nav) if latest_nav else None,
                "record_count": nav_count,
            },
            "performance": {
                "return_1m": _pct(metrics.get("return_1m")),
                "return_3m": _pct(metrics.get("return_3m")),
                "return_6m": _pct(metrics.get("return_6m")),
                "return_1y": _pct(metrics.get("return_1y")),
                "max_drawdown_1y": _pct(metrics.get("max_drawdown_1y")),
                "sharpe_ratio_1y": metrics.get("sharpe_ratio_1y"),
            },
        }

    def _manager_snapshot(self, manager: Manager) -> Dict[str, Any]:
        products = self.db.query(Product).filter(Product.manager_id == manager.id).limit(20).all()
        product_snaps = [self._product_snapshot(product) for product in products[:8]]
        return {
            "id": manager.id,
            "name": manager.manager_name,
            "short_name": manager.short_name,
            "pool_category": manager.pool_category,
            "primary_strategy": manager.primary_strategy,
            "rating": manager.rating,
            "aum_range": manager.aum_range,
            "has_penalty": manager.has_penalty,
            "product_count": len(products),
            "representative_products": product_snaps,
        }

    def _build_data(self, key: str, path: str) -> Dict[str, Any]:
        builders = {
            "dashboard": self._dashboard_data,
            "managers": self._manager_data,
            "products": self._product_data,
            "product-detail": lambda: self._product_detail_data(path),
            "portfolios": self._portfolio_data,
            "projects": self._project_data,
            "ranking": self._market_data,
            "analysis": self._analysis_data,
            "attribution": self._attribution_data,
            "alerts": self._alert_data,
            "ai-reports": self._report_data,
            "documents": self._document_data,
            "tasks": self._task_data,
        }
        try:
            return builders.get(key, self._dashboard_data)()
        except Exception as exc:
            logger.exception(f"构建Copilot上下文失败: module={key}, error={exc}")
            return {"summary": {"数据状态": "读取失败"}, "error": str(exc)}

    def _dashboard_data(self) -> Dict[str, Any]:
        today = date.today()
        return {
            "summary": {
                "管理人总数": self.db.query(Manager).filter(Manager.is_deleted == False).count(),
                "产品总数": self.db.query(Product).count(),
                "组合总数": self.db.query(Portfolio).filter(Portfolio.is_deleted == False).count(),
                "一级项目": self.db.query(Project).filter(Project.is_deleted == False).count(),
                "待办任务": self.db.query(Task).filter(Task.status.in_(["pending", "in_progress"])).count(),
                "逾期任务": self.db.query(Task).filter(Task.due_date < today, Task.status.in_(["pending", "in_progress"])).count(),
            },
            "manager_pool": _rows_to_dict(self.db.query(Manager.pool_category, func.count(Manager.id)).filter(Manager.is_deleted == False).group_by(Manager.pool_category).all()),
            "product_strategy": _rows_to_dict(self.db.query(Product.strategy_type, func.count(Product.id)).group_by(Product.strategy_type).all()),
            "recent_negative_news": [
                {"title": n.title, "manager": n.manager.manager_name if n.manager else None, "date": _safe_value(n.publish_date)}
                for n in self.db.query(NewsArticle).filter(NewsArticle.sentiment == "negative").order_by(desc(NewsArticle.publish_date)).limit(5).all()
            ],
        }

    def _manager_data(self) -> Dict[str, Any]:
        return {
            "summary": {
                "管理人总数": self.db.query(Manager).filter(Manager.is_deleted == False).count(),
                "有处罚记录": self.db.query(Manager).filter(Manager.is_deleted == False, Manager.has_penalty == True).count(),
                "未评级": self.db.query(Manager).filter(Manager.is_deleted == False, Manager.rating.in_(["unrated", "", None])).count(),
            },
            "by_pool": _rows_to_dict(self.db.query(Manager.pool_category, func.count(Manager.id)).filter(Manager.is_deleted == False).group_by(Manager.pool_category).all()),
            "by_strategy": _rows_to_dict(self.db.query(Manager.primary_strategy, func.count(Manager.id)).filter(Manager.is_deleted == False).group_by(Manager.primary_strategy).all()),
            "by_rating": _rows_to_dict(self.db.query(Manager.rating, func.count(Manager.id)).filter(Manager.is_deleted == False).group_by(Manager.rating).all()),
            "manager_performance_leaders": self._manager_performance_leaders()[:10],
            "recent_managers": [
                {"name": m.manager_name, "pool": m.pool_category, "strategy": m.primary_strategy, "rating": m.rating}
                for m in self.db.query(Manager).filter(Manager.is_deleted == False).order_by(desc(Manager.created_at)).limit(8).all()
            ],
        }

    def _product_data(self) -> Dict[str, Any]:
        latest_nav_date = self.db.query(func.max(NavData.nav_date)).scalar()
        top_returns = self._top_products_from_raw()[:12]
        return {
            "summary": {
                "产品总数": self.db.query(Product).count(),
                "运行中": self.db.query(Product).filter(Product.status == "active").count(),
                "在投产品": self.db.query(Product).filter(Product.is_invested == True).count(),
                "最新净值日": _safe_value(latest_nav_date) or "无",
            },
            "by_status": _rows_to_dict(self.db.query(Product.status, func.count(Product.id)).group_by(Product.status).all()),
            "by_strategy": _rows_to_dict(self.db.query(Product.strategy_type, func.count(Product.id)).group_by(Product.strategy_type).all()),
            "top_1y_return": top_returns,
            "manager_performance_leaders": self._manager_performance_leaders()[:8],
        }

    def _product_detail_data(self, path: str) -> Dict[str, Any]:
        product_id = None
        try:
            product_id = int(path.strip("/").split("/")[1])
        except Exception:
            pass
        if not product_id:
            return self._product_data()

        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"summary": {"产品状态": "未找到"}}
        perf = self.db.query(FundPerformance).filter(FundPerformance.product_id == product.id).order_by(desc(FundPerformance.update_date)).first()
        ext = self.db.query(FundExtendedInfo).filter(FundExtendedInfo.product_id == product.id).first()
        latest_nav = self.db.query(NavData).filter(NavData.product_id == product.id).order_by(desc(NavData.nav_date)).first()
        return {
            "summary": {
                "产品名称": product.product_name,
                "管理人": product.manager.manager_name if product.manager else "-",
                "策略": product.strategy_type or ext.strategy_level1 if ext else product.strategy_type,
                "状态": product.status,
                "最新净值日": _safe_value(latest_nav.nav_date) if latest_nav else "无",
                "最新单位净值": _safe_value(latest_nav.unit_nav) if latest_nav else "无",
            },
            "performance": {
                "return_1m": perf.return_1m if perf else None,
                "return_3m": perf.return_3m if perf else None,
                "return_1y": perf.return_1y if perf else None,
                "max_drawdown_1y": perf.max_drawdown_1y if perf else None,
                "volatility_1y": perf.volatility_1y if perf else None,
                "sharpe_ratio_1y": perf.sharpe_ratio_1y if perf else None,
            },
            "fees": {"management_fee": _safe_value(product.management_fee), "performance_fee": _safe_value(product.performance_fee)},
        }

    def _portfolio_data(self) -> Dict[str, Any]:
        portfolios = self.db.query(Portfolio).filter(Portfolio.is_deleted == False).order_by(desc(Portfolio.updated_at)).limit(8).all()
        return {
            "summary": {
                "组合总数": self.db.query(Portfolio).filter(Portfolio.is_deleted == False).count(),
                "生效组合": self.db.query(Portfolio).filter(Portfolio.is_deleted == False, Portfolio.status == "active").count(),
                "组合成分数": self.db.query(PortfolioComponent).filter(PortfolioComponent.is_active == True).count(),
            },
            "by_status": _rows_to_dict(self.db.query(Portfolio.status, func.count(Portfolio.id)).filter(Portfolio.is_deleted == False).group_by(Portfolio.status).all()),
            "recent_portfolios": [
                {
                    "name": p.name,
                    "type": p.portfolio_type,
                    "status": p.status,
                    "latest_nav": _safe_value(self._latest_portfolio_nav(p.id)),
                }
                for p in portfolios
            ],
        }

    def _latest_portfolio_nav(self, portfolio_id: int) -> Any:
        row = (
            self.db.query(PortfolioNav.unit_nav)
            .filter(PortfolioNav.portfolio_id == portfolio_id)
            .order_by(desc(PortfolioNav.nav_date))
            .first()
        )
        return row[0] if row else None

    def _project_data(self) -> Dict[str, Any]:
        return {
            "summary": {
                "项目总数": self.db.query(Project).filter(Project.is_deleted == False).count(),
                "尽调中": self.db.query(Project).filter(Project.is_deleted == False, Project.stage == "DUE_DILIGENCE").count(),
                "投后项目": self.db.query(Project).filter(Project.is_deleted == False, Project.stage == "POST_INVESTMENT").count(),
            },
            "by_stage": _rows_to_dict(self.db.query(Project.stage, func.count(Project.id)).filter(Project.is_deleted == False).group_by(Project.stage).all()),
            "by_industry": _rows_to_dict(self.db.query(Project.industry, func.count(Project.id)).filter(Project.is_deleted == False).group_by(Project.industry).all()),
            "recent_projects": [
                {"name": p.project_name, "stage": _safe_value(p.stage), "industry": _safe_value(p.industry), "investment_amount": _safe_value(p.investment_amount)}
                for p in self.db.query(Project).filter(Project.is_deleted == False).order_by(desc(Project.updated_at)).limit(8).all()
            ],
        }

    def _market_data(self) -> Dict[str, Any]:
        strategy_rows = self._strategy_recent_performance()
        top_products = self._top_products_from_raw()
        usable_3m = sum(item["available_3m_count"] for item in strategy_rows)
        usable_1y = sum(item["available_1y_count"] for item in strategy_rows)

        return {
            "summary": {
                "业绩样本": self.db.query(FundPerformance).count(),
                "可计算近3月样本": usable_3m,
                "可计算近1年样本": usable_1y,
                "近1年正收益产品": len([item for item in top_products if (item.get("return_1y_value") or 0) > 0]),
                "近1年回撤超10%": len([item for item in top_products if (item.get("max_drawdown_1y_value") or 0) < -0.1]),
            },
            "data_quality": {
                "note": "结构化收益风险字段为空时，已从 raw_data.nav_perf.prices 按累计净值回溯计算。",
                "metric_source": "FundPerformance结构化字段优先；缺失时使用原始净值序列计算30/90/180/365天收益。",
            },
            "strategy_recent_performance": strategy_rows,
            "top_return_1y": top_products[:10],
        }

    def _strategy_recent_performance(self) -> List[Dict[str, Any]]:
        if self._strategy_performance_cache is not None:
            return self._strategy_performance_cache
        cached = _read_global_cache("strategy_recent_performance")
        if cached is not None:
            self._strategy_performance_cache = cached
            return self._strategy_performance_cache

        rows = (
            self.db.query(Product, FundPerformance, FundExtendedInfo)
            .join(FundPerformance, FundPerformance.product_id == Product.id)
            .outerjoin(FundExtendedInfo, FundExtendedInfo.product_id == Product.id)
            .all()
        )

        grouped: Dict[str, Dict[str, Any]] = {}
        for product, perf, ext in rows:
            strategy = self._resolve_strategy(product, perf, ext)
            metrics = self._performance_metrics(perf)
            bucket = grouped.setdefault(
                strategy,
                {
                    "strategy": strategy,
                    "sample_count": 0,
                    "return_1m": [],
                    "return_3m": [],
                    "return_6m": [],
                    "return_1y": [],
                    "max_drawdown_1y": [],
                    "sharpe_ratio_1y": [],
                },
            )
            bucket["sample_count"] += 1
            for key, value in metrics.items():
                if key in bucket:
                    bucket[key].append(value)

        result: List[Dict[str, Any]] = []
        for bucket in grouped.values():
            avg_1m = _avg(bucket["return_1m"])
            avg_3m = _avg(bucket["return_3m"])
            avg_6m = _avg(bucket["return_6m"])
            avg_1y = _avg(bucket["return_1y"])
            avg_dd = _avg(bucket["max_drawdown_1y"])
            avg_sharpe = _avg(bucket["sharpe_ratio_1y"])
            result.append(
                {
                    "strategy": bucket["strategy"],
                    "sample_count": bucket["sample_count"],
                    "available_3m_count": len([v for v in bucket["return_3m"] if v is not None]),
                    "available_1y_count": len([v for v in bucket["return_1y"] if v is not None]),
                    "avg_return_1m": _pct(avg_1m),
                    "avg_return_3m": _pct(avg_3m),
                    "avg_return_6m": _pct(avg_6m),
                    "avg_return_1y": _pct(avg_1y),
                    "avg_max_drawdown_1y": _pct(avg_dd),
                    "avg_sharpe_ratio_1y": None if avg_sharpe is None else round(avg_sharpe, 3),
                    "score_hint": self._strategy_score(avg_3m, avg_6m, avg_1y, avg_dd),
                }
            )

        self._strategy_performance_cache = _write_global_cache("strategy_recent_performance", sorted(
            result,
            key=lambda item: (
                item["available_3m_count"] > 0,
                item["score_hint"] if item["score_hint"] is not None else -999,
            ),
            reverse=True,
        ))
        return self._strategy_performance_cache

    def _top_products_from_raw(self) -> List[Dict[str, Any]]:
        if self._top_products_cache is not None:
            return self._top_products_cache
        cached = _read_global_cache("top_products_from_raw")
        if cached is not None:
            self._top_products_cache = cached
            return self._top_products_cache

        rows = (
            self.db.query(Product, FundPerformance, FundExtendedInfo)
            .join(FundPerformance, FundPerformance.product_id == Product.id)
            .outerjoin(FundExtendedInfo, FundExtendedInfo.product_id == Product.id)
            .all()
        )
        products: List[Dict[str, Any]] = []
        for product, perf, ext in rows:
            metrics = self._performance_metrics(perf)
            products.append(
                {
                    "product": product.product_name,
                    "strategy": self._resolve_strategy(product, perf, ext),
                    "return_3m": _pct(metrics["return_3m"]),
                    "return_1y": _pct(metrics["return_1y"]),
                    "max_drawdown_1y": _pct(metrics["max_drawdown_1y"]),
                    "return_1y_value": metrics["return_1y"],
                    "max_drawdown_1y_value": metrics["max_drawdown_1y"],
                }
            )
        products.sort(key=lambda item: item["return_1y_value"] if item["return_1y_value"] is not None else -999, reverse=True)
        self._top_products_cache = _write_global_cache("top_products_from_raw", products)
        return self._top_products_cache

    def _manager_performance_leaders(self) -> List[Dict[str, Any]]:
        if self._manager_leaders_cache is not None:
            return self._manager_leaders_cache
        cached = _read_global_cache("manager_performance_leaders")
        if cached is not None:
            self._manager_leaders_cache = cached
            return self._manager_leaders_cache

        products = self._top_products_from_raw()
        grouped: Dict[str, Dict[str, Any]] = {}
        product_by_name = {p.product_name: p for p in self.db.query(Product).all()}

        for item in products:
            product = product_by_name.get(item["product"])
            if not product or not product.manager:
                continue
            manager_name = product.manager.manager_name
            bucket = grouped.setdefault(
                manager_name,
                {
                    "manager": manager_name,
                    "manager_id": product.manager.id,
                    "pool_category": product.manager.pool_category,
                    "primary_strategy": product.manager.primary_strategy,
                    "product_count": 0,
                    "available_1y_count": 0,
                    "return_1y_values": [],
                    "drawdown_1y_values": [],
                    "top_products": [],
                },
            )
            bucket["product_count"] += 1
            if item.get("return_1y_value") is not None:
                bucket["available_1y_count"] += 1
                bucket["return_1y_values"].append(item["return_1y_value"])
            if item.get("max_drawdown_1y_value") is not None:
                bucket["drawdown_1y_values"].append(item["max_drawdown_1y_value"])
            if len(bucket["top_products"]) < 3:
                bucket["top_products"].append(
                    {
                        "product": item["product"],
                        "strategy": item["strategy"],
                        "return_1y": item["return_1y"],
                        "max_drawdown_1y": item["max_drawdown_1y"],
                    }
                )

        leaders: List[Dict[str, Any]] = []
        for bucket in grouped.values():
            avg_return = _avg(bucket["return_1y_values"])
            avg_drawdown = _avg(bucket["drawdown_1y_values"])
            leaders.append(
                {
                    "manager": bucket["manager"],
                    "manager_id": bucket["manager_id"],
                    "pool_category": bucket["pool_category"],
                    "primary_strategy": bucket["primary_strategy"],
                    "product_count": bucket["product_count"],
                    "available_1y_count": bucket["available_1y_count"],
                    "avg_return_1y": _pct(avg_return),
                    "avg_max_drawdown_1y": _pct(avg_drawdown),
                    "score_hint": self._strategy_score(None, None, avg_return, avg_drawdown),
                    "top_products": bucket["top_products"],
                }
            )

        self._manager_leaders_cache = _write_global_cache("manager_performance_leaders", sorted(
            leaders,
            key=lambda item: (
                item["available_1y_count"],
                item["score_hint"] if item["score_hint"] is not None else -999,
            ),
            reverse=True,
        ))
        return self._manager_leaders_cache

    def _resolve_strategy(self, product: Product, perf: FundPerformance, ext: Optional[FundExtendedInfo]) -> str:
        if product.strategy_type:
            return product.strategy_type
        if ext and ext.strategy_level1:
            return ext.strategy_level1
        raw = perf.raw_data or {}
        detail = raw.get("detail") if isinstance(raw, dict) else {}
        strategies = detail.get("strategy") if isinstance(detail, dict) else []
        if isinstance(strategies, list) and strategies:
            name = strategies[0].get("strategy_name")
            if name:
                return name
        return "未分类"

    def _performance_metrics(self, perf: FundPerformance) -> Dict[str, Optional[float]]:
        prices = self._raw_prices(perf.raw_data)
        return {
            "return_1m": _as_float(perf.return_1m) if perf.return_1m is not None else self._series_return_from_prices(prices, 30),
            "return_3m": _as_float(perf.return_3m) if perf.return_3m is not None else self._series_return_from_prices(prices, 90),
            "return_6m": _as_float(perf.return_6m) if perf.return_6m is not None else self._series_return_from_prices(prices, 180),
            "return_1y": _as_float(perf.return_1y) if perf.return_1y is not None else self._series_return_from_prices(prices, 365),
            "max_drawdown_1y": _as_float(perf.max_drawdown_1y) if perf.max_drawdown_1y is not None else self._series_drawdown_from_prices(prices, 365),
            "sharpe_ratio_1y": _as_float(perf.sharpe_ratio_1y) if perf.sharpe_ratio_1y is not None else self._raw_nav_metric(perf.raw_data, "sharpe_ratio"),
        }

    def _raw_nav_metric(self, raw_data: Any, key: str) -> Optional[float]:
        raw = raw_data or {}
        nav_perf = raw.get("nav_perf") if isinstance(raw, dict) else {}
        if not isinstance(nav_perf, dict):
            return None
        return _as_float(nav_perf.get(key))

    def _series_return(self, raw_data: Any, days: int) -> Optional[float]:
        return self._series_return_from_prices(self._raw_prices(raw_data), days)

    def _series_return_from_prices(self, prices: List[tuple[date, float]], days: int) -> Optional[float]:
        if len(prices) < 2:
            return None
        latest_date, latest_value = prices[-1]
        target_date = latest_date - timedelta(days=days)
        base = None
        for item_date, item_value in reversed(prices):
            if item_date <= target_date:
                base = item_value
                break
        if base is None:
            base = prices[0][1]
        if not base:
            return None
        return round(latest_value / base - 1, 6)

    def _series_drawdown(self, raw_data: Any, days: int) -> Optional[float]:
        return self._series_drawdown_from_prices(self._raw_prices(raw_data), days)

    def _series_drawdown_from_prices(self, prices: List[tuple[date, float]], days: int) -> Optional[float]:
        if len(prices) < 2:
            return None
        latest_date = prices[-1][0]
        scoped = [(d, v) for d, v in prices if d >= latest_date - timedelta(days=days)]
        if len(scoped) < 2:
            scoped = prices
        peak = scoped[0][1]
        max_drawdown = 0.0
        for _, value in scoped:
            if value > peak:
                peak = value
            if peak:
                drawdown = value / peak - 1
                if drawdown < max_drawdown:
                    max_drawdown = drawdown
        return round(max_drawdown, 6)

    def _raw_prices(self, raw_data: Any) -> List[tuple[date, float]]:
        raw = raw_data or {}
        nav_perf = raw.get("nav_perf") if isinstance(raw, dict) else {}
        raw_prices = nav_perf.get("prices") if isinstance(nav_perf, dict) else []
        prices: List[tuple[date, float]] = []
        if not isinstance(raw_prices, list):
            return prices
        for item in raw_prices:
            if not isinstance(item, dict):
                continue
            item_date = _parse_series_date(item.get("pd"))
            value = _as_float(item.get("cnw")) or _as_float(item.get("cn")) or _as_float(item.get("nav"))
            if item_date and value is not None and value > 0:
                prices.append((item_date, value))
        return sorted(prices, key=lambda item: item[0])

    def _strategy_score(
        self,
        return_3m: Optional[float],
        return_6m: Optional[float],
        return_1y: Optional[float],
        drawdown_1y: Optional[float],
    ) -> Optional[float]:
        returns = [v for v in [return_3m, return_6m, return_1y] if v is not None]
        if not returns:
            return None
        score = returns[0] * 0.5
        if len(returns) > 1:
            score += returns[1] * 0.3
        if len(returns) > 2:
            score += returns[2] * 0.2
        if drawdown_1y is not None:
            score += drawdown_1y * 0.2
        return round(score, 6)

    def _analysis_data(self) -> Dict[str, Any]:
        return {
            "summary": {
                "已分析产品": self.db.query(Product).filter(Product.analysis_data.isnot(None)).count(),
                "未分析产品": self.db.query(Product).filter(Product.analysis_data.is_(None)).count(),
                "业绩样本": self.db.query(FundPerformance).count(),
            },
            "recent_updates": [
                {"product": p.product_name, "last_analysis_update": _safe_value(p.last_analysis_update), "strategy": p.strategy_type}
                for p in self.db.query(Product).filter(Product.analysis_data.isnot(None)).order_by(desc(Product.last_analysis_update)).limit(8).all()
            ],
        }

    def _attribution_data(self) -> Dict[str, Any]:
        return {
            "summary": {
                "已有归因产品": self.db.query(Product).filter(Product.attribution_data.isnot(None)).count(),
                "缺少归因产品": self.db.query(Product).filter(Product.attribution_data.is_(None)).count(),
            },
            "by_strategy": _rows_to_dict(self.db.query(Product.strategy_type, func.count(Product.id)).filter(Product.attribution_data.isnot(None)).group_by(Product.strategy_type).all()),
        }

    def _alert_data(self) -> Dict[str, Any]:
        try:
            summary = AlertService(self.db).get_alerts_summary()
            alerts = summary.get("alerts", [])[:10] if isinstance(summary, dict) else []
            by_level = summary.get("by_level", {}) if isinstance(summary, dict) else {}
            return {
                "summary": {
                    "严重预警": by_level.get("critical", 0),
                    "警告预警": by_level.get("warning", 0),
                    "提示预警": by_level.get("info", 0),
                    "预警总数": len(alerts),
                },
                "recent_alerts": alerts,
            }
        except Exception as exc:
            logger.warning(f"预警上下文读取失败: {exc}")
            return {"summary": {"预警状态": "读取失败"}, "recent_alerts": []}

    def _report_data(self) -> Dict[str, Any]:
        return {
            "summary": {
                "报告总数": self.db.query(AIReport).count(),
                "草稿": self.db.query(AIReport).filter(AIReport.status == "draft").count(),
                "已发布": self.db.query(AIReport).filter(AIReport.status == "published").count(),
            },
            "by_type": _rows_to_dict(self.db.query(AIReport.report_type, func.count(AIReport.id)).group_by(AIReport.report_type).all()),
            "recent_reports": [
                {"title": r.title, "type": r.report_type, "status": r.status, "updated_at": _safe_value(r.updated_at)}
                for r in self.db.query(AIReport).order_by(desc(AIReport.updated_at)).limit(8).all()
            ],
        }

    def _document_data(self) -> Dict[str, Any]:
        return {
            "summary": {
                "资料总数": self.db.query(Document).count(),
                "未关联资料": self.db.query(Document).filter(Document.relation_type.is_(None)).count(),
            },
            "by_category": _rows_to_dict(self.db.query(Document.category, func.count(Document.id)).group_by(Document.category).all()),
            "by_relation": _rows_to_dict(self.db.query(Document.relation_type, func.count(Document.id)).group_by(Document.relation_type).all()),
            "recent_documents": [
                {"title": d.title or d.filename, "category": _safe_value(d.category), "relation": _safe_value(d.relation_type), "uploaded_at": _safe_value(d.uploaded_at)}
                for d in self.db.query(Document).order_by(desc(Document.uploaded_at)).limit(8).all()
            ],
        }

    def _task_data(self) -> Dict[str, Any]:
        today = date.today()
        return {
            "summary": {
                "任务总数": self.db.query(Task).count(),
                "待处理": self.db.query(Task).filter(Task.status == "pending").count(),
                "进行中": self.db.query(Task).filter(Task.status == "in_progress").count(),
                "已逾期": self.db.query(Task).filter(Task.due_date < today, Task.status.in_(["pending", "in_progress"])).count(),
            },
            "by_priority": _rows_to_dict(self.db.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()),
            "upcoming_tasks": [
                {"title": t.title, "priority": t.priority, "status": t.status, "due_date": _safe_value(t.due_date)}
                for t in self.db.query(Task).filter(Task.status.in_(["pending", "in_progress"])).order_by(Task.due_date.asc()).limit(10).all()
            ],
        }
