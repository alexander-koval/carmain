from pydantic import BaseModel


from fastapi_users import schemas


class User(schemas.BaseUser[int]):
    pass


class UserRead(User):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
