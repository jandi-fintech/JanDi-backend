# File: domain/user/user_schema.py
from pydantic import BaseModel, validator, EmailStr


# ────────────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    
    """사용자 등록 요청 스키마"""
    
    username    : str     
    password1   : str     
    password2   : str     
    email       : EmailStr 

    @validator('username', 'password1', 'password2', 'email')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('빈 값은 허용되지 않습니다.')
        return v

    @validator('password2')
    def passwords_match(cls, v, values):
        if 'password1' in values and v != values['password1']:
            raise ValueError('비밀번호가 일치하지 않습니다.')
        return v


# ────────────────────────────────────────────────────────────────────────────
class Token(BaseModel):
    
    """JWT 토큰 응답 스키마"""
    
    access_token: str  
    token_type  : str 
    username    : str  


# ────────────────────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    
    """사용자 정보 응답 스키마"""
    
    id      : int     
    username: str   
    email   : str   

    class Config:
        orm_mode = True   


# ────────────────────────────────────────────────────────────────────────────
class LoginCheckOut(BaseModel):
    
    """로그인 상태 응답 스키마"""
    
    username    : str   
    is_logged_in: bool = True   
