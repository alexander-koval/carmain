from fastapi import FastAPI


carmain = FastAPI()


@carmain.get('/')
async def welcome() -> dict:
    return {"message": "Welcome User"}
