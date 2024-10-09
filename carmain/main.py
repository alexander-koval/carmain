from fastapi import FastAPI
from sqladmin import Admin
from carmain.core.db import engine

carmain = FastAPI(title="Carmain", debug=True)
admin = Admin(carmain, engine=engine)


@carmain.get("/")
async def welcome() -> dict:
    return {"message": "Welcome User"}
