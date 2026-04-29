"""
Review SDK API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter()


class AccessVerifyRequest(BaseModel):
    token: str


class AnnotationCreate(BaseModel):
    app: str
    version: str
    reviewer: dict
    page: dict
    context: dict
    anchor: dict
    artifacts: dict
    review: dict
    createdAt: str


class SubmissionCreate(BaseModel):
    annotation_id: int
    status: str
    comment: Optional[str] = None


@router.get("/review-permission")
async def check_review_permission(
    app: Optional[str] = None,
    version: Optional[str] = None,
    reviewerId: Optional[str] = None,
    reviewerRole: Optional[str] = None
):
    """检查审批权限（转发到外部系统）"""
    import httpx
    try:
        params = {}
        if app: params['app'] = app
        if version: params['version'] = version
        if reviewerId: params['reviewerId'] = reviewerId
        if reviewerRole: params['reviewerRole'] = reviewerRole

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                "https://rvw.yz314.com:9000/api/review-permission",
                params=params,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return {"canReview": False}
    except:
        return {"canReview": False}


@router.post("/access/verify")
async def verify_access(request: AccessVerifyRequest):
    """验证访问令牌"""
    import httpx
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                "https://rvw.yz314.com:9000/api/access/verify",
                json={"token": request.token},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return {"valid": False}
    except:
        return {"valid": False}


@router.get("/annotations")
async def get_annotations(
    page_url: Optional[str] = None,
    page: Optional[str] = None,
    version: Optional[str] = None,
    app: Optional[str] = None,
    reviewerId: Optional[str] = None,
    accessToken: Optional[str] = None
):
    """获取标注列表（转发到外部系统）"""
    import httpx
    try:
        params = {}
        if page_url: params['page_url'] = page_url
        if page: params['page'] = page
        if version: params['version'] = version
        if app: params['app'] = app
        if reviewerId: params['reviewerId'] = reviewerId
        if accessToken: params['accessToken'] = accessToken

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                "https://rvw.yz314.com:9000/api/annotations",
                params=params,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return []
    except:
        return []


@router.post("/annotations")
async def create_annotation(
    annotation: AnnotationCreate,
    accessToken: Optional[str] = None
):
    """创建标注（转发到外部系统）"""
    import httpx
    try:
        headers = {}
        if accessToken:
            headers['x-review-access-token'] = accessToken

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                "https://rvw.yz314.com:9000/api/annotations",
                json=annotation.dict(),
                headers=headers,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return {"error": "创建失败", "status": response.status_code}
    except Exception as e:
        return {"error": str(e)}


@router.post("/submissions")
async def create_submission(
    submission: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交审批"""
    return {
        "id": 1,
        "annotation_id": submission.annotation_id,
        "status": submission.status,
        "created_at": datetime.now().isoformat()
    }


@router.post("/access-tokens/generate")
async def generate_token():
    """生成访问令牌（转发到外部系统）"""
    import httpx
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                "https://rvw.yz314.com:9000/api/access-tokens/generate",
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return {"ok": False, "error": "生成失败"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/artifacts/{annotation_id}/{artifact_type}")
async def get_artifact(
    annotation_id: int,
    artifact_type: str,
    accessToken: Optional[str] = None
):
    """获取制品（转发到外部系统）"""
    import httpx
    try:
        params = {}
        if accessToken:
            params['accessToken'] = accessToken

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"https://rvw.yz314.com:9000/api/artifacts/{annotation_id}/{artifact_type}",
                params=params,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except:
        return
