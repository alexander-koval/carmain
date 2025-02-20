from fastapi_users import FastAPIUsers

from carmain.core import backend
from carmain.models.users import User
from carmain.schema import user_schema

fastapi_users = FastAPIUsers[User, int](
    backend.get_user_manager, backend.get_backends()
)

current_user = fastapi_users.current_user(get_enabled_backends=backend.get_backends)
current_active_user = fastapi_users.current_user(
    active=True, get_enabled_backends=backend.get_backends
)
current_active_verified_user = fastapi_users.current_user(
    active=True, verified=True, get_enabled_backends=backend.get_backends
)
current_superuser = fastapi_users.current_user(
    active=True, superuser=True, get_enabled_backends=backend.get_backends
)


auth_router = fastapi_users.get_auth_router(backend.cookie_backend)
register_router = fastapi_users.get_register_router(
    user_schema.User, user_schema.UserCreate
)
verify_router = fastapi_users.get_verify_router(user_schema.User)
reset_password_router = fastapi_users.get_reset_password_router()

users_router = fastapi_users.get_users_router(
    user_schema.User, user_schema.UserUpdate, requires_verification=True
)

# from carmain.schema.auth import SignUp, SignIn
# from carmain.services.auth_service import AuthService
#
# router = APIRouter(prefix="/auth", tags=["auth"])
#
#
# @router.post("/sign-up")  # , response_model=User)
# async def create_user(
#     user_info: SignUp,
#     service: Annotated[
#         AuthService,
#         Depends(AuthService),
#     ],
# ):
#     user = await service.sing_up(user_info)
#     return JSONResponse(status_code=201, content={"status": "ok"})
#
#
# @router.post("/login")
# async def login(
#     form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
#     service: Annotated[
#         AuthService,
#         Depends(AuthService),
#     ],
# ):
#     user_info: SignIn = SignIn(email=form_data.username, password=form_data.password)
#     user = await service.sign_in(user_info)
#
#     if not user or user.is_active is False:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user"
#         )
#
#     return {"email": user.email}
