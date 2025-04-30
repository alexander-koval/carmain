import logging
from fastapi import Depends
from sqladmin import Admin
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from carmain.admin.items import MaintenanceItemAdmin, UserMaintenanceItemAdmin
from carmain.admin.records import ServiceRecordAdmin
from carmain.admin.users import UserAdmin, AccessTokenAdmin
from carmain.admin.vehicles import VehicleAdmin
from carmain.core import database
from carmain.models.users import User
from carmain.routers.v1 import auth_router, vehicle_router
from carmain.views import auth_router as auth_view_router
from carmain.views.v1 import vehicle_view, maintenance_view
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

carmain = FastAPI(title="Carmain", debug=True)

carmain.mount("/static", StaticFiles(directory="carmain/static"), name="static")

admin = Admin(carmain, engine=database.engine)
admin.add_view(UserAdmin)
admin.add_view(AccessTokenAdmin)
admin.add_view(MaintenanceItemAdmin)
admin.add_view(UserMaintenanceItemAdmin)
admin.add_view(VehicleAdmin)
admin.add_view(ServiceRecordAdmin)

carmain.include_router(auth_view_router.auth_view_router)
carmain.include_router(auth_router.auth_router, prefix="/v1/auth", tags=["auth"])
carmain.include_router(
    auth_router.register_router, prefix="/v1/auth", tags=["register"]
)
carmain.include_router(auth_router.verify_router, prefix="/v1/auth", tags=["verify"])
carmain.include_router(
    auth_router.reset_password_router, prefix="/auth_reset", tags=["reset_password"]
)
carmain.include_router(auth_router.users_router, prefix="/users", tags=["users"])
carmain.include_router(vehicle_router.vehicle_router)
carmain.include_router(vehicle_view.vehicle_router)
carmain.include_router(maintenance_view.router)


# @carmain.get("/")
# async def welcome(user: User = Depends(auth_router.current_user)) -> dict:
#     return {"message": f"Welcome {user.email}"}

templates = Jinja2Templates(directory="carmain/templates")


@carmain.get("/")
async def index(
    request: Request, 
    user: User = Depends(auth_router.optional_user),
    vehicle_service: vehicle_view.VehicleService = Depends()
):
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    if user.is_active and user.is_verified:
        vehicles = await vehicle_service.get_user_vehicles()
        return templates.TemplateResponse(
            request=request, 
            name="garage.html", 
            context={"vehicles": vehicles, "user": user}
        )
    return RedirectResponse(url="/auth/login", status_code=302)


@carmain.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


# Middleware для обработки 401 ошибок и перенаправления на страницу входа
@carmain.middleware("http")
async def auth_middleware(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/auth/login", status_code=302)
    return response


# def custom_openapi():
#     # if carmain.openapi_schema:
#     #     return carmain.openapi_schema
#     openapi_schema = get_openapi(
#         title="Carmain",
#         version="0.0.1",
#         description="Car Maintenance Tool",
#         routes=carmain.routes,
#     )
#     openapi_schema["components"]["securitySchemes"] = {
#         "cookieAuth": {"type": "apiKey", "in": "cookie", "name": "token"}
#     }
#     openapi_schema["security"] = [{"cookieAuth": []}]
#     carmain.openapi_schema = openapi_schema
#     return carmain.openapi_schema
#
#
# carmain.openapi = custom_openapi
