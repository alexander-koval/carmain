from datetime import datetime

from pydantic import BaseModel


class SignIn(BaseModel):
    email__eq: str
    password: str


class SignUp(BaseModel):
    email: str
    password: str


# class SignInResponse(BaseModel):
#     access_token: str
#     expiration: datetime
#     user_info: User
