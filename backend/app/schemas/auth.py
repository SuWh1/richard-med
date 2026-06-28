from pydantic import BaseModel, ConfigDict


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None
    role: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut
