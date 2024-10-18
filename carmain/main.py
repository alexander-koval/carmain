from fastapi import FastAPI, Depends
from sqladmin import Admin

from carmain.admin.users import UserAdmin, AccessTokenAdmin
from carmain.core import database
from carmain.models.users import User
from carmain.routers import auth

carmain = FastAPI(title="Carmain", debug=True)

admin = Admin(carmain, engine=database.engine)
admin.add_view(UserAdmin)
admin.add_view(AccessTokenAdmin)


carmain.include_router(auth.auth_router, prefix="/auth", tags=["auth"])
carmain.include_router(auth.register_router, prefix="/auth", tags=["register"])
carmain.include_router(auth.verify_router, prefix="/auth", tags=["verify"])
carmain.include_router(
    auth.reset_password_router, prefix="/auth_reset", tags=["reset_password"]
)
carmain.include_router(auth.users_router, prefix="/users", tags=["users"])


@carmain.get("/")
async def welcome(user: User = Depends(auth.current_user)) -> dict:
    return {"message": f"Welcome {user.email}"}
