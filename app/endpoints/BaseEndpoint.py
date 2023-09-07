from fastapi import APIRouter

router = APIRouter()


@router.get("/api/testing")
def get_is_server_working():
    return {"message": "server is running!"}
