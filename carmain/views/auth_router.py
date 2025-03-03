from fastapi import APIRouter, Depends
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.authentication import Strategy
from fastapi_users import models

from carmain.core.backend import get_user_manager, UserManager, cookie_backend
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from urllib.parse import quote


auth_view_router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="carmain/templates")


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
