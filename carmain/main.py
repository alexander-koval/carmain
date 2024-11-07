import logging
from fastapi import FastAPI, Depends, Request, status
from fastapi.exceptions import RequestValidationError
from sqladmin import Admin

from carmain.admin.items import MaintenanceItemAdmin, UserMaintenanceItemAdmin
from carmain.admin.records import ServiceRecordAdmin
from carmain.admin.users import UserAdmin, AccessTokenAdmin
from carmain.admin.vehicles import VehicleAdmin
from carmain.core import database
from carmain.models.users import User
from carmain.routers import auth_router, vehicle_router
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

carmain = FastAPI(title="Carmain", debug=True)

admin = Admin(carmain, engine=database.engine)
admin.add_view(UserAdmin)
admin.add_view(AccessTokenAdmin)
admin.add_view(MaintenanceItemAdmin)
admin.add_view(UserMaintenanceItemAdmin)
admin.add_view(VehicleAdmin)
admin.add_view(ServiceRecordAdmin)


carmain.include_router(auth_router.auth_router, prefix="/auth", tags=["auth"])
carmain.include_router(auth_router.register_router, prefix="/auth", tags=["register"])
carmain.include_router(auth_router.verify_router, prefix="/auth", tags=["verify"])
carmain.include_router(
    auth_router.reset_password_router, prefix="/auth_reset", tags=["reset_password"]
)
carmain.include_router(auth_router.users_router, prefix="/users", tags=["users"])
carmain.include_router(vehicle_router.vehicle_router)


@carmain.get("/")
async def welcome(user: User = Depends(auth_router.current_user)) -> dict:
    return {"message": f"Welcome {user.email}"}


@carmain.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


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
