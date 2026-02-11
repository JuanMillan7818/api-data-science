from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.services.centenarios import centenarios_service
from app.schemas import info_variables as schemas
import math

router = APIRouter()


# response_model: Define el esquema Pydantic utilizado para validar y serializar la respuesta.
# Garantiza que el cliente reciba solo los campos definidos en VariableListResponse.
@router.get("/variables", response_model=schemas.VariableListResponse)
async def get_variables(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None
):
    """
    Obtiene lista paginada de variables.
    Permite filtrar por nombre o etiqueta mediante el parámetro 'search'.
    """
    try:
        # Obtener todas las variables del servicio
        all_vars = centenarios_service.get_variables_from_dictionary()

        # Filtrar por término de búsqueda si se proporciona
        if search:
            search_lower = search.lower()
            all_vars = [
                v for v in all_vars
                if search_lower in str(v.get("variable", "")).lower() or
                search_lower in str(v.get("variable_label", "")).lower() or
                any(search_lower in k.lower() for k in v.get("keywords", []))
            ]

        # Crear objetos Variable (Pydantic models)
        variable_objects = []
        for v in all_vars:
            categories_data = v.get("categories", [])
            categories_objs = [
                schemas.Category(code=c['code'], value=c['value']) for c in categories_data
            ]

            variable_objects.append(
                schemas.Variable(
                    variable=str(v.get("variable", "")),
                    variable_label=str(v.get("variable_label", "")) if v.get(
                        "variable_label") else None,
                    dtype=v.get("dtype", "unknown"),
                    categories=categories_objs,
                    keywords=v.get("keywords", []),
                    valid_percentage=v.get("valid_percentage", 0.0),
                    null_count=v.get("null_count", 0),
                    non_null_count=v.get("non_null_count", 0),
                    total_rows=v.get("total_rows", 0)
                )
            )

        # Paginación
        total = len(variable_objects)
        start = (page - 1) * size
        end = start + size
        items = variable_objects[start:end]

        has_more = end < total

        return schemas.VariableListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            has_more=has_more
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# response_model: Esquema para la respuesta de completitud.
# Filtra y documenta autom&aacute;ticamente la estructura de salida (CompletenessResponse).
@router.get("/completeness", response_model=schemas.CompletenessResponse)
async def get_completeness_stats(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    dtype: Optional[str] = Query(
        None, description="Filtrar por tipo de variable")
):
    """
    Obtiene estadísticas de completitud para las variables.
    Soporta filtrado por dtype (numeric, categorical, etc.) y paginación.
    """
    try:
        completeness_data = centenarios_service.get_variable_completeness(
            page=page, size=size, dtype=dtype
        )

        items = [
            schemas.CompletenessItem(**item) for item in completeness_data['items']
        ]

        return schemas.CompletenessResponse(
            items=items,
            total=completeness_data['total'],
            page=completeness_data['page'],
            size=completeness_data['size'],
            has_more=completeness_data['has_more']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# response_model: Esquema para estadísticas globales.
# Asegura que la API retorne un objeto StatsResponse válido.
@router.get("/stats", response_model=schemas.StatsResponse)
async def get_stats():
    """
    Obtiene estadísticas globales del dataset.
    Retorna conteos por tipo de dato y porcentaje de completitud global.
    """
    try:
        stats = centenarios_service.get_variable_stats()
        return schemas.StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
