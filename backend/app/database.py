import logging
from datetime import datetime
from sqlalchemy import DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import BASE_DIR, settings

logger = logging.getLogger(__name__)

def _create_robust_engine():
    db_url = settings.DATABASE_URL
    if "sqlite" in db_url.lower():
        return create_engine(db_url, connect_args={"check_same_thread": False})
    
    # 尝试连接 MySQL
    try:
        eng = create_engine(db_url, pool_recycle=3600)
        with eng.connect() as conn:
            pass
        return eng
    except Exception as e:
        logger.warning(f"无法连接 MySQL 服务 ({e})，系统已自动无缝切换为本地 SQLite 数据库，实现零配置免装运行！")
        sqlite_file = BASE_DIR / "data" / "lab_agent.db"
        sqlite_file.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(f"sqlite:///{sqlite_file.as_posix()}", connect_args={"check_same_thread": False})

engine = _create_robust_engine()

# 数据库session会话的连接工厂
SessionLocal = sessionmaker(bind=engine, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="主键ID", sort_order=-1
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间", sort_order=1
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间", sort_order=2
    )
