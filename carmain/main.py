from fastapi import FastAPI, Request, Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import Authenticator
from fastapi_users.router import get_auth_router
from sqladmin import Admin
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from carmain.admin.users import UserAdmin, AccessTokenAdmin
from carmain.core import database, backend
from carmain.models.users import User
from carmain.routers import auth

carmain = FastAPI(title="Carmain", debug=True)

admin = Admin(carmain, engine=database.engine)
admin.add_view(UserAdmin)
admin.add_view(AccessTokenAdmin)

# carmain.include_router(auth.router)
carmain.include_router(
    # get_auth_router(
    #     backend.auth_backend,
    #     backend.get_user_manager,
    #     Authenticator([backend.auth_backend], backend.get_user_manager),
    # ),
    auth.fastapi_users.get_auth_router(backend.auth_backend),
    prefix="/auth",
    tags=["auth"],
)

# TODO: register router
# carmain.include_router(
#     auth.fastapi_users.get_register_router()
# )

# TODO: verify router
# carmain.include_router(auth.fastapi_users.get_verify_router())

carmain.include_router(
    auth.fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

# @carmain.middleware("http")
# async def validate_user(request: Request, call_next):
#     print(
#         request.session
#     )  # <--- Error: 'AssertionError: SessionMiddleware must be installed to access request.session'
#     response = await call_next(request)
#     return response


@carmain.get("/")
async def welcome(user: User = Depends(auth.current_user)) -> dict:
    return {"message": f"Welcome {user.email}"}


# carmain.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
# carmain.add_middleware(CORSMiddleware, allow_origins=["*"])
# carmain.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
