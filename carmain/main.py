from fastapi import FastAPI
from sqladmin import Admin

from carmain.admin.users import UserAdmin
from carmain.core.db import engine
from carmain.routers import auth

carmain = FastAPI(title="Carmain", debug=True)
admin = Admin(carmain, engine=engine)
admin.add_view(UserAdmin)

carmain.include_router(auth.router)


@carmain.get("/")
async def welcome() -> dict:
    return {"message": "Welcome User"}
