"""
AI Copilot API.
"""
from typing import Any, Dict, List, Optional
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.copilot_attachment_service import extract_attachment
from app.services.copilot_service import CopilotService, MODULE_PROFILES
from app.services.llm_service import llm_service

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


class ChatMessage(BaseModel):
    role: str
    content: str


class CopilotChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    path: Optional[str] = None
    module_key: Optional[str] = None
    provider: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)
    stream: bool = Field(default=False, description="是否使用流式输出(打字机效果)")


@router.get("/modules", summary="获取Copilot支持模块")
async def get_copilot_modules(
    current_user: User = Depends(get_current_user),
):
    return [
        {
            "key": key,
            "name": profile["name"],
            "role": profile["role"],
            "questions": profile["questions"],
            "planning": profile["planning"],
        }
        for key, profile in MODULE_PROFILES.items()
    ]


@router.get("/providers", summary="获取Copilot模型通道")
async def get_copilot_providers(
    current_user: User = Depends(get_current_user),
):
    return llm_service.get_provider_options()


@router.get("/context", summary="获取当前模块Copilot上下文")
async def get_copilot_context(
    path: Optional[str] = None,
    module_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CopilotService(db)
    return service.get_context(path=path, module_key=module_key)


@router.post("/chat", summary="发送Copilot问答")
async def chat_with_copilot(
    payload: CopilotChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    service = CopilotService(db)
    history: List[Dict[str, str]] = [item.model_dump() for item in payload.history]
    
    if payload.stream:
        # 返回流式响应
        return StreamingResponse(
            service.chat_stream(
                question=question,
                path=payload.path,
                module_key=payload.module_key,
                provider=payload.provider,
                history=history,
            ),
            media_type="text/event-stream",
        )
    else:
        # 返回普通响应
        return service.chat(
            question=question,
            path=payload.path,
            module_key=payload.module_key,
            provider=payload.provider,
            history=history,
        )


@router.post("/chat-with-files", summary="发送带附件的Copilot问答")
async def chat_with_copilot_files(
    question: str = Form(...),
    path: Optional[str] = Form(None),
    module_key: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),
    history: str = Form("[]"),
    files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = question.strip()
    if not question and not files:
        raise HTTPException(status_code=400, detail="问题或附件不能为空")

    try:
        parsed_history = json.loads(history or "[]")
        if not isinstance(parsed_history, list):
            parsed_history = []
    except json.JSONDecodeError:
        parsed_history = []

    attachments: List[Dict[str, Any]] = []
    for upload in files[:5]:
        data = await upload.read()
        attachments.append(extract_attachment(upload.filename or "未命名附件", upload.content_type, data))

    service = CopilotService(db)
    return service.chat(
        question=question or "请分析我上传的附件，并结合当前模块数据给出判断。",
        path=path,
        module_key=module_key,
        provider=provider,
        history=[
            {"role": item.get("role"), "content": item.get("content")}
            for item in parsed_history
            if isinstance(item, dict)
        ],
        attachments=attachments,
    )
