from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.centenarios import centenarios_service
from app.schemas import info_variables as schemas

router = APIRouter(
    prefix="/categorical",
    tags=["categorical"]
)


@router.get("/", response_model=schemas.CategoricalStatsResponse)
async def get_categorical_stats(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None
):
    """
    Obtiene estadísticas detalladas para variables categóricas (top valores).
    """
    try:
        stats = centenarios_service.get_categorical_stats(
            page=page, size=size, search=search)
        return schemas.CategoricalStatsResponse(**stats)
    except Exception as e:
        print(f"Error procesando request categorical: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
