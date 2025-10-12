from fastapi import APIRouter

from src.controllers.home_controller import get_version, get_welcome_message, health

router = APIRouter()


@router.get("/")
def welcome():
    return get_welcome_message()


@router.get("/health")
def health_check():
    return health()


@router.get("/version")
def version():
    return get_version()
