from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.response import Response

class BusinessException(Exception):
    """自定义的业务异常"""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(message)

async def bussiness_excpetion_hadler(request: Request, exc: BusinessException):
    """自定义业务异常处理器"""
    return JSONResponse(
        status_code=200,
        content=Response.error(code=exc.code, message=exc.message).model_dump(),
    )

async def http_excpetion_hadler(request: Request, exc: HTTPException):
    """Http异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=Response.error(code=exc.status_code, message=exc.detail).model_dump(),
    )

async def validation_excpetion_hadler(request: Request, exc: RequestValidationError):
    """参数异常处理器：展示具体缺失或错误的字段"""
    errors = exc.errors()
    details = []
    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []) if x not in ("body", "query"))
        msg = err.get("msg", "")
        details.append(f"{loc}: {msg}" if loc else msg)
    msg_str = "请求参数校验错误: " + "; ".join(details) if details else "请求参数校验错误"
    return JSONResponse(
        status_code=422,
        content=Response.error(code=422, message=msg_str).model_dump(),
    )

async def global_excpetion_hadler(request: Request, exc: Exception):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content=Response.error(code=500, message="服务器内部错误").model_dump(),
    )
