from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from carmain.core.db import get_async_session
from carmain.models.users import User

from carmain.schema.auth import SignUp
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
    print(user)
    return JSONResponse(status_code=201, content={"status": "ok"})
