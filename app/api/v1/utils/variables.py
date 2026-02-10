from fastapi import APIRouter
from app.services.centenarios import centenarios_service

router = APIRouter(
    prefix="/variables",
    tags=["variables"]
)

@router.get("/")
def list_variables_from_dictionary():
    # USAR EL SERVICIO
    return centenarios_service.get_variables_from_dictionary()
    
