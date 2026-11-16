import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.config import BASE_DIR, UPLOAD_DIR
from app.database import Base, SessionLocal, engine
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.api import api_router
from app.common.exceptions import (
    BusinessException,
    bussiness_excpetion_hadler,
    http_excpetion_hadler,
    validation_excpetion_hadler,
    global_excpetion_hadler,
)
from app.services import reservation_service, kb_service, seed_service

logger = logging.getLogger(__name__)

# 创建数据表并自动填充初始数据
try:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db_session:
        seed_service.seed_initial_data(db_session)
except Exception as e:
    logger.warning(f"数据表初始化提示: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 异步预热向量库，避免阻塞服务启动
    asyncio.create_task(asyncio.to_thread(kb_service.warmup))
    # 启动项目开启异步的扫描任务
    task = asyncio.create_task(reservation_service.run_expire_scan())
    yield
    task.cancel()  # 关闭项目同时取消异步任务

app = FastAPI(title="智能实验室预约系统 API", lifespan=lifespan)

# 注册异常处理器
app.add_exception_handler(BusinessException, bussiness_excpetion_hadler)
app.add_exception_handler(HTTPException, http_excpetion_hadler)
app.add_exception_handler(RequestValidationError, validation_excpetion_hadler)
app.add_exception_handler(Exception, global_excpetion_hadler)

# 跨域配置
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router)

# 挂载上传文件目录
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 挂载前端打包后的静态资源 (SPA 完整单机托管)
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_spa(full_path: str):
        # 排除 API 请求、上传资源及文档接口
        if full_path.startswith("api/") or full_path.startswith("uploads/") or full_path in ("docs", "redoc", "openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")
        
        target = FRONTEND_DIST / full_path
        if target.is_file():
            return FileResponse(target)
        # 默认返回 SPA 单页入口 index.html
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/", include_in_schema=False)
    def index():
        return RedirectResponse(url="/docs")
