from pydantic import BaseModel, EmailStr

from fastapi_users import schemas


class UserSchema(schemas.BaseUser[int]):
    pass


class UserRead(UserSchema):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class SignUpFormData(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
