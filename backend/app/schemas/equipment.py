from typing import Any
from pydantic import BaseModel, ConfigDict, model_validator

class EquipmentResponse(BaseModel):
    id: int
    lab_id: int
    lab_name: str | None = None
    name: str
    description: str | None = None
    img: str | None = None
    spec: str | None = None
    quantity: int
    status: int

    model_config = ConfigDict(from_attributes=True)

class EquipmentCreateRequest(BaseModel):
    lab_id: int
    name: str
    description: str | None = None
    img: str | None = None
    spec: str | None = None
    quantity: int = 1
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
            if data.get("quantity") is not None and str(data.get("quantity")).strip() != "":
                try:
                    data["quantity"] = int(data["quantity"])
                except (ValueError, TypeError):
                    pass
        return data

class EquipmentUpdateRequest(BaseModel):
    lab_id: int | None = None
    name: str | None = None
    description: str | None = None
    img: str | None = None
    spec: str | None = None
    quantity: int | None = None
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
            if "quantity" in data:
                val = data.get("quantity")
                if val is None or str(val).strip() == "":
                    data["quantity"] = None
                else:
                    try:
                        data["quantity"] = int(val)
                    except (ValueError, TypeError):
                        pass
        return data
