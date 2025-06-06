import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends
from markupsafe import Markup
from sqladmin import Admin
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from carmain.admin.items import MaintenanceItemAdmin, UserMaintenanceItemAdmin
from carmain.admin.records import ServiceRecordAdmin
from carmain.admin.users import UserAdmin, AccessTokenAdmin
from carmain.admin.vehicles import VehicleAdmin
from carmain.bootstrap import create_initial_maintenance_items
from carmain.core import database
from carmain.models.users import User
from carmain.routers.v1 import auth_router, vehicle_router
from carmain.views import auth_router as auth_view_router
from carmain.views.v1 import vehicle_view, maintenance_view, service_view
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create initial maintenance items
    logger.info("Application startup: initializing maintenance items")
    
    # Использование get_async_session корректным образом
    async for session in database.get_async_session():
        try:
            await create_initial_maintenance_items(session)
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise
    
    yield
    
    # Shutdown: cleanup resources if needed
    logger.info("Application shutdown: cleaning up resources")


carmain = FastAPI(title="Carmain", debug=True, lifespan=lifespan)

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
carmain.include_router(service_view.router)


# @carmain.get("/")
# async def welcome(user: User = Depends(auth_router.current_user)) -> dict:
#     return {"message": f"Welcome {user.email}"}

templates = Jinja2Templates(directory="carmain/templates")


def to_json_filter(value):
    if isinstance(value, uuid.UUID):
        return Markup(json.dumps(str(value)))
    return Markup(json.dumps(value))


templates.env.filters["tojson"] = to_json_filter

# def to_json_filter(value):
#     """
#     Преобразует объект Python в строку JSON, безопасную для вставки в HTML/JS.
#     Использует markupsafe.Markup для предотвращения двойного HTML-экранирования.
#     """
#     return Markup(json.dumps(value))
#
#
# templates.env.filters["tojson"] = to_json_filter


@carmain.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {"status": "healthy", "service": "carmain"}


@carmain.get("/")
async def index(
    request: Request,
    user: User = Depends(auth_router.optional_user),
    vehicle_service: vehicle_view.VehicleService = Depends(),
):
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)

    if user.is_active and user.is_verified:
        vehicles = await vehicle_service.get_user_vehicles()
        return templates.TemplateResponse(
            request=request,
            name="garage.html",
            context={"vehicles": vehicles, "user": user},
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
