from pydantic import BaseModel, Field, EmailStr

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    tokenType: str = "Bearer"
    username: str
    role: str

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    email: str  # Use simple str to avoid strict EmailStr validation if we want max compatibility, but let's do a basic check
    role: str

class PasswordResetRequest(BaseModel):
    newPassword: str = Field(..., min_length=8, max_length=100)
