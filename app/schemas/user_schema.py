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


class UserLogin(BaseModel):
    email: EmailStr
    password: str
