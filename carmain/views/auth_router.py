from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form

from fastapi_users.authentication import Strategy
from fastapi_users import models, exceptions
from fastapi_users.router.common import ErrorCode
from pydantic import EmailStr
from starlette.responses import RedirectResponse

from carmain.core.backend import get_user_manager, UserManager, cookie_backend
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from urllib.parse import quote

from carmain.models.users import User
from carmain.routers.v1.auth_router import current_active_verified_user
from carmain.schema.user_schema import UserCreate, SignUpFormData

auth_view_router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="carmain/templates")


async def get_signup_form_data(
    email: EmailStr = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
) -> SignUpFormData:
    return SignUpFormData(
        email=email, password=password, confirm_password=confirm_password
    )


@auth_view_router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@auth_view_router.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html")


@auth_view_router.post("/login")
async def login_action(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
    strategy: Strategy[models.UP, models.ID] = Depends(cookie_backend.get_strategy),
):
    user = await user_manager.authenticate(credentials)
    if user is None or not user.is_active:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid credentials"}
        )
    else:
        response = await cookie_backend.login(strategy, user)
        response.headers["location"] = quote(str("/"), safe=":/%#?=@[]!$&'()*+,;")
        response.status_code = status.HTTP_303_SEE_OTHER
        return response


@auth_view_router.get("/logout")
async def logout_action(
    request: Request,
    user: User = Depends(current_active_verified_user),
    strategy: Strategy[models.UP, models.ID] = Depends(cookie_backend.get_strategy),
):
    token = request.headers.get("token")
    response = await cookie_backend.logout(strategy, user, token)
    response.headers["location"] = quote(str("/"), safe=":/%#?=@[]!$&'()*+,;")
    response.status_code = status.HTTP_303_SEE_OTHER
    return response


@auth_view_router.post("/signup")
async def signup_action(
    request: Request,
    form_data: SignUpFormData = Depends(get_signup_form_data),
    user_manager: UserManager = Depends(get_user_manager),
):
    user_create = UserCreate(email=form_data.email, password=form_data.password)
    try:
        await user_manager.create(user_create, safe=True, request=request)
    except exceptions.UserAlreadyExists as e:
        return templates.TemplateResponse(
            "signup.html", {"request": request, "error": "Account already exists"}
        )
    except exceptions.InvalidPasswordException as e:
        return templates.TemplateResponse(
            "signup.html", {"request": request, "error": e.reason}
        )
    return RedirectResponse("/auth/login", status_code=303)
