from fastapi import FastAPI, Request
from fastapi_users.router import get_auth_router
from sqladmin import Admin
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from carmain.admin.users import UserAdmin, AccessTokenAdmin
from carmain.core.db import engine, settings
from carmain.routers import auth

carmain = FastAPI(title="Carmain", debug=True)

admin = Admin(carmain, engine=engine)
admin.add_view(UserAdmin)
admin.add_view(AccessTokenAdmin)

carmain.include_router(auth.router)
# carmain.include_router(get_auth_router())


@carmain.middleware("http")
async def validate_user(request: Request, call_next):
    print(
        request.session
    )  # <--- Error: 'AssertionError: SessionMiddleware must be installed to access request.session'
    response = await call_next(request)
    return response


@carmain.get("/")
async def welcome(request: Request) -> dict:
    return {"message": f"Welcome {request.session}"}


carmain.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
# carmain.add_middleware(CORSMiddleware, allow_origins=["*"])
# carmain.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
