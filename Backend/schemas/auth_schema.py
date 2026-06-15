from pydantic import BaseModel, EmailStr

# Signup ke liye
class SignupSchema(BaseModel):
    username: str
    email: str
    password: str

# Login ke liye
class LoginSchema(BaseModel):
    email: str
    password: str

# Token response ke liye
class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"