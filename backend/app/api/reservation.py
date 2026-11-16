from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.reservation import AuditReservationRequest, ReservationCreateRequest
from app.services import reservation_service

router = APIRouter(prefix="/reservation", tags=["预约相关接口"])

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

@router.post("")
def create_reservation(
    data: ReservationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交预约申请"""
    reservation_service.create_reservation(db, current_user, data)
    return Response.success(message="预约提交成功，请等待管理员审核")

@router.get("/list")
def get_reservation_page_list(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """预约列表（学生看个人，管理员看全部）"""
    int_status = _parse_status(status)
    res = reservation_service.get_reservation_page_list(
        db, current_user, page, page_size, int_status
    )
    return Response.success(data=res)

@router.put("/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """学生取消个人预约"""
    reservation_service.cancel_reservation(db, current_user, reservation_id)
    return Response.success(message="取消预约成功")

@router.put("/{reservation_id}/audit")
def audit_reservation(
    reservation_id: int,
    data: AuditReservationRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员审核预约（1通过 / 2拒绝）"""
    reservation_service.audit_reservation(db, reservation_id, data.status)
    return Response.success(message="审核操作成功")
