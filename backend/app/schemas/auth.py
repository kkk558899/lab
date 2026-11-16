from pydantic import BaseModel
from app.schemas.user import UserResponse

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str | None = None

class LoginResponse(BaseModel):
    token: str
    user: UserResponse
