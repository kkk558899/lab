from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user, get_optional_user
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.equipment import EquipmentCreateRequest, EquipmentUpdateRequest
from app.schemas.lab import LabCreateRequest, LabUpdateRequest
from app.schemas.reservation import AuditReservationRequest, ReservationCreateRequest
from app.schemas.user import PasswordUpdateRequest, UserCreateRequest, UserUpdateRequest
from app.services import (
    equipment_service,
    lab_service,
    reservation_service,
    user_service,
)

compat_router = APIRouter(tags=["兼容接口"])

def _parse_int(val: Any) -> int | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        return int(s)
    except (ValueError, TypeError):
        return None

def _parse_status(status: Any) -> int | None:
    if status is None:
        return None
    s = str(status).upper().strip()
    if not s:
        return None
    status_map = {
        "PENDING": 0,
        "0": 0,
        "APPROVED": 1,
        "1": 1,
        "REJECTED": 2,
        "2": 2,
        "CANCELLED": 3,
        "3": 3,
    }
    return status_map.get(s, None)

# ----------------- 仪表盘统计 -----------------
@compat_router.get("/dashboard/stats")
def get_dashboard_stats(
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    lab_count = db.query(Lab).count()
    device_count = db.query(Equipment).count()
    booking_count = db.query(Reservation).count()
    pending_count = db.query(Reservation).filter(Reservation.status == 0).count()
    return Response.success(
        data={
            "lab_count": lab_count,
            "device_count": device_count,
            "booking_count": booking_count,
            "pending_count": pending_count,
        }
    )

# ----------------- 用户信息兼容 -----------------
@compat_router.get("/auth/me")
def get_auth_me(current_user: User = Depends(get_current_user)):
    return Response.success(data=user_service.get_user_info(current_user))

@compat_router.get("/users")
def get_users(
    page: int = 1,
    page_size: int = 10,
    size: int | None = None,
    keywords: str | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    actual_size = size if size is not None else page_size
    res = user_service.get_user_page_list(db, page, actual_size, keywords)
    return Response.success(data=res)

@compat_router.post("/users")
def add_user(
    data: UserCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.create_user(db, data)
    return Response.success(data=res)

@compat_router.put("/users/profile")
def update_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = user_service.update_user_info(db, current_user, data)
    return Response.success(data=res)

@compat_router.put("/users/password")
def update_pwd(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_service.update_password(db, current_user, data)
    return Response.success(message="密码修改成功")

@compat_router.put("/users/{id}")
def update_user_by_id(
    id: int,
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.update_user(db, id, data)
    return Response.success(data=res)

@compat_router.delete("/users/{id}")
def delete_user_by_id(
    id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user_service.delete_user(db, id, current_user)
    return Response.success(message="删除成功")

# ----------------- 实验室兼容 /labs -----------------
@compat_router.get("/labs")
def get_labs(
    page: int = 1,
    page_size: int = 10,
    size: int | None = None,
    keywords: str | None = None,
    name: str | None = None,
    location: str | None = None,
    status: str | None = None,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    actual_size = size if size is not None else page_size
    kw = (keywords or name or "").strip() or None
    int_status = _parse_int(status)
    res = lab_service.get_lab_page_list(db, page, actual_size, kw, int_status)
    return Response.success(data=res)

@compat_router.get("/labs/all")
def get_labs_all(
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    res = lab_service.get_lab_page_list(db, page=1, page_size=100, status=1)
    return Response.success(data=res.list)

@compat_router.get("/labs/{id}")
def get_lab_by_id(
    id: int,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    res = lab_service.get_lab(db, id)
    return Response.success(data=res)

@compat_router.post("/labs")
def create_lab_compat(
    data: LabCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = lab_service.create_lab(db, data)
    return Response.success(data=res)

@compat_router.put("/labs/{id}")
def update_lab_compat(
    id: int,
    data: LabUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = lab_service.update_lab(db, id, data)
    return Response.success(data=res)

@compat_router.delete("/labs/{id}")
def delete_lab_compat(
    id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    lab_service.delete_lab(db, id)
    return Response.success(message="删除成功")

# ----------------- 设备兼容 /devices -----------------
@compat_router.get("/devices")
def get_devices(
    page: int = 1,
    page_size: int = 10,
    size: int | None = None,
    keywords: str | None = None,
    lab_id: str | None = None,
    status: str | None = None,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    actual_size = size if size is not None else page_size
    int_lab_id = _parse_int(lab_id)
    int_status = _parse_int(status)
    res = equipment_service.get_equipment_page_list(
        db, page, actual_size, keywords, int_lab_id
    )
    return Response.success(data=res)

@compat_router.get("/devices/lab/{lab_id}")
def get_devices_by_lab(
    lab_id: int,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    res = equipment_service.get_equipment_page_list(
        db, page=1, page_size=100, lab_id=lab_id
    )
    return Response.success(data=res.list)

@compat_router.post("/devices")
def create_device_compat(
    data: EquipmentCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = equipment_service.create_equipment(db, data)
    return Response.success(data=res)

@compat_router.put("/devices/{id}")
def update_device_compat(
    id: int,
    data: EquipmentUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = equipment_service.update_equipment(db, id, data)
    return Response.success(data=res)

@compat_router.delete("/devices/{id}")
def delete_device_compat(
    id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    equipment_service.delete_equipment(db, id)
    return Response.success(message="删除成功")

# ----------------- 预约兼容 /bookings -----------------
@compat_router.get("/bookings")
def get_bookings(
    page: int = 1,
    page_size: int = 10,
    size: int | None = None,
    status: str | None = None,
    user_name: str | None = None,
    lab_name: str | None = None,
    booking_date: str | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    actual_size = size if size is not None else page_size
    int_status = _parse_status(status)
    res = reservation_service.get_reservation_page_list(
        db, current_user, page, actual_size, int_status
    )
    return Response.success(data=res)

@compat_router.get("/bookings/my")
def get_my_bookings(
    page: int = 1,
    page_size: int = 10,
    size: int | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    actual_size = size if size is not None else page_size
    int_status = _parse_status(status)
    res = reservation_service.get_reservation_page_list(
        db, current_user, page, actual_size, int_status
    )
    return Response.success(data=res)

@compat_router.post("/bookings")
def create_booking_compat(
    data: ReservationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reservation_service.create_reservation(db, current_user, data)
    return Response.success(message="预约提交成功，请等待管理员审核")

@compat_router.put("/bookings/{id}/audit")
def audit_booking_compat(
    id: int,
    data: AuditReservationRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    reservation_service.audit_reservation(db, id, data.status)
    return Response.success(message="审核操作成功")

@compat_router.put("/bookings/{id}/cancel")
def cancel_booking_compat(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reservation_service.cancel_reservation(db, current_user, id)
    return Response.success(message="取消预约成功")

# ----------------- AI 辅助接口 -----------------
@compat_router.get("/ai/prompts")
def get_ai_prompts():
    return Response.success(
        data=[
            "现在有哪些开放的实验室？",
            "哪个实验室有 RTX4090 显卡？",
            "请介绍一下实验室的安全规范与规则。",
            "帮我查一下明天下午计算机实验室是否可以预约？",
        ]
    )

@compat_router.get("/ai/knowledge")
def get_ai_knowledge():
    return Response.success(
        data=[
            {"name": "预约规则.md", "status": "已构建向量索引", "size": "277 B"},
            {"name": "开放时间.md", "status": "已构建向量索引", "size": "285 B"},
            {"name": "安全规范.md", "status": "已构建向量索引", "size": "279 B"},
            {"name": "设备使用.md", "status": "已构建向量索引", "size": "241 B"},
        ]
    )
