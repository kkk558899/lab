from typing import Any
from pydantic import BaseModel, ConfigDict, model_validator

class ReservationCreateRequest(BaseModel):
    lab_id: int
    equipment_id: int | None = None
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    remark: str | None = None

    # 兼容前端表单字段
    booking_date: str | None = None
    time_slot: str | None = None
    reason: str | None = None
    member_count: int | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 兼容 booking_date -> date
            if not data.get("date") and data.get("booking_date"):
                data["date"] = data["booking_date"]
            # 兼容 reason -> remark
            if not data.get("remark") and data.get("reason"):
                data["remark"] = data["reason"]
            # 兼容 time_slot -> start_time, end_time
            if not data.get("start_time") or not data.get("end_time"):
                slot = (data.get("time_slot") or "").upper()
                if slot == "MORNING":
                    data.setdefault("start_time", "08:30")
                    data.setdefault("end_time", "12:00")
                elif slot == "AFTERNOON":
                    data.setdefault("start_time", "13:30")
                    data.setdefault("end_time", "17:30")
                elif slot == "EVENING":
                    data.setdefault("start_time", "18:30")
                    data.setdefault("end_time", "21:30")
            # 截取到 HH:MM 格式保证时间比较一致
            if data.get("start_time") and len(str(data["start_time"])) > 5:
                data["start_time"] = str(data["start_time"])[:5]
            if data.get("end_time") and len(str(data["end_time"])) > 5:
                data["end_time"] = str(data["end_time"])[:5]
        return data

    @model_validator(mode="after")
    def validate_required_fields(self):
        if not self.date:
            raise ValueError("预约日期(date或booking_date)不能为空")
        if not self.start_time or not self.end_time:
            raise ValueError("预约时段(start_time/end_time 或 time_slot)不能为空")
        return self

class ReservationResponse(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None
    lab_id: int
    lab_name: str | None = None
    equipment_id: int | None = None
    equipment_name: str | None = None
    type: str | None = None
    date: str
    start_time: str
    end_time: str
    remark: str | None = None
    status: int

    # 兼容前端字段
    booking_date: str | None = None
    time_slot: str | None = None
    reason: str | None = None
    member_count: int = 1
    audit_remark: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_compat_fields(self):
        if not self.booking_date:
            self.booking_date = self.date
        if not self.reason:
            self.reason = self.remark
        if not self.time_slot:
            if self.start_time and ("08:" in self.start_time or "09:" in self.start_time):
                self.time_slot = "MORNING"
            elif self.start_time and ("13:" in self.start_time or "14:" in self.start_time):
                self.time_slot = "AFTERNOON"
            elif self.start_time and ("18:" in self.start_time or "19:" in self.start_time):
                self.time_slot = "EVENING"
            else:
                self.time_slot = f"{self.start_time}-{self.end_time}"
        return self

class AuditReservationRequest(BaseModel):
    status: int  # 1-通过，2-拒绝
    audit_remark: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_status(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw = data.get("status")
            if isinstance(raw, str):
                s = raw.upper().strip()
                if s in ("APPROVED", "1", "PASS", "SUCCESS"):
                    data["status"] = 1
                elif s in ("REJECTED", "2", "REFUSE", "REJECT"):
                    data["status"] = 2
                else:
                    try:
                        data["status"] = int(s)
                    except (ValueError, TypeError):
                        pass
        return data
