from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal['FARMER', 'REGULATOR', 'SUPPLIER', 'ADMIN']
    
    # User role with restricted literals and normalization
    @field_validator('role', mode ='before')
    @classmethod
    def normalize_role(cls, v):
        return v.upper()

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be 72 bytes or fewer.')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be 72 bytes or fewer.')
        return v
