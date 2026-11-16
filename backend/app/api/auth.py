import json
import re
import urllib.parse
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.response import Response
from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["权限验证"])

@router.post(
    "/login",
    summary="用户登录（兼容 JSON 与 Form 表单）",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string", "example": "admin"},
                            "password": {"type": "string", "example": "123456"},
                        },
                        "required": ["username", "password"],
                    }
                },
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string", "example": "admin"},
                            "password": {"type": "string", "example": "123456"},
                        },
                        "required": ["username", "password"],
                    }
                },
            }
        }
    },
)
async def login(request: Request, db: Session = Depends(get_db)):
    raw_bytes = await request.body()
    raw_text = raw_bytes.decode("utf-8", errors="ignore").strip()

    username = ""
    password = ""

    # 1. 尝试 JSON 解析
    try:
        obj = json.loads(raw_text)
        if isinstance(obj, dict):
            username = str(obj.get("username") or obj.get("account") or "").strip()
            password = str(obj.get("password") or "").strip()
    except Exception:
        pass

    # 2. 尝试 Form urlencoded 解析 (Swagger UI Authorize 弹窗)
    if not username and not password:
        qs = urllib.parse.parse_qs(raw_text)
        if "username" in qs or "password" in qs or "account" in qs:
            username = str((qs.get("username") or qs.get("account") or [""])[0]).strip()
            password = str((qs.get("password") or [""])[0]).strip()

    # 3. 兜底正则提取（应对命令行/脚本引号转义丢失的情况）
    if not username or not password:
        u_m = re.search(r'["\']?(?:username|account)["\']?\s*[:=]\s*["\']?([^,"\';}\s&]+)', raw_text)
        p_m = re.search(r'["\']?password["\']?\s*[:=]\s*["\']?([^,"\';}\s&]+)', raw_text)
        if u_m:
            username = u_m.group(1).strip()
        if p_m:
            password = p_m.group(1).strip()

    if not username or not password:
        raise BusinessException(message="请输入用户名和密码", code=400)

    data = LoginRequest(username=username, password=password)
    result = auth_service.login(db, data)

    # 满足前端 Vue (res.data.token), Swagger OAuth2 (access_token, token_type), 及常规规范
    return {
        "code": 200,
        "message": "登录成功",
        "data": result.model_dump(),
        "token": result.token,
        "access_token": result.token,
        "token_type": "bearer",
    }

@router.post("/register", summary="用户注册")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    auth_service.register(db, data)
    return Response.success(message="注册成功")
