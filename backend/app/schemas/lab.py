from typing import Any
from pydantic import BaseModel, ConfigDict, model_validator

class LabResponse(BaseModel):
    id: int
    name: str
    location: str | None = None
    capacity: int
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int

    model_config = ConfigDict(from_attributes=True)

class LabCreateRequest(BaseModel):
    name: str
    location: str | None = None
    capacity: int = 0
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int = 1

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("status") is not None and str(data.get("status")).strip() != "":
                try:
                    data["status"] = int(data["status"])
                except (ValueError, TypeError):
                    data["status"] = 1
            if data.get("capacity") is not None and str(data.get("capacity")).strip() != "":
                try:
                    data["capacity"] = int(data["capacity"])
                except (ValueError, TypeError):
                    pass
        return data

class LabUpdateRequest(BaseModel):
    name: str | None = None
    location: str | None = None
    capacity: int | None = None
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "status" in data:
                val = data.get("status")
                if val is None or str(val).strip() == "":
                    data["status"] = None
                else:
                    try:
                        data["status"] = int(val)
                    except (ValueError, TypeError):
                        data["status"] = None
            if "capacity" in data:
                val = data.get("capacity")
                if val is None or str(val).strip() == "":
                    data["capacity"] = None
                else:
                    try:
                        data["capacity"] = int(val)
                    except (ValueError, TypeError):
                        pass
        return data
