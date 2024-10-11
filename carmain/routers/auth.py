from typing import Annotated

from fastapi import APIRouter, Depends, Response, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from carmain.core.db import get_async_session
from carmain.models.users import User

from carmain.schema.auth import SignUp, SignIn
from carmain.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sign-up")  # , response_model=User)
async def create_user(
    user_info: SignUp,
    service: Annotated[
        AuthService,
        Depends(AuthService),
    ],
):
    user = await service.sing_up(user_info)
    return JSONResponse(status_code=201, content={"status": "ok"})


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[
        AuthService,
        Depends(AuthService),
    ],
):
    user_info: SignIn = SignIn(email=form_data.username, password=form_data.password)
    user = await service.sign_in(user_info)

    if not user or user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user"
        )

    return {"email": user.email}
