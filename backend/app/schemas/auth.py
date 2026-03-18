from pydantic import BaseModel

class RegisterRequest(BaseModel):
    full_name: str
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    full_name: str
    username: str
    role: str

    @classmethod
    def from_user(cls, user):
        return cls(id=str(user.id), full_name=user.full_name, username=user.username, role=user.role)

class AuthResponse(BaseModel):
    token: str
    user: UserResponse
