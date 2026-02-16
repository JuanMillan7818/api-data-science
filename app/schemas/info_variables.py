from typing import List, Optional, Any
from pydantic import BaseModel


class Category(BaseModel):
    """
    Representa una categoría dentro de una variable categórica.
    """
    code: str  # Código interno de la categoría (ej: "1")
    value: str  # Valor legible de la categoría (ej: "Femenino")


class Variable(BaseModel):
    """
    Información detallada de una variable, incluyendo metadatos y estadísticas básicas.
    """
    variable: str  # Nombre identificador de la variable
    variable_label: Optional[str] = None  # Etiqueta descriptiva
    # Tipo de dato inferido (numeric, categorical, etc.)
    dtype: Optional[str] = "unknown"
    # Lista de categorías si es aplicable
    categories: Optional[List[Category]] = []
    keywords: Optional[List[str]] = []  # Palabras clave asociadas
    # Porcentaje de datos válidos (no nulos)
    valid_percentage: Optional[float] = 0.0
    null_count: Optional[int] = 0  # Conteo absoluto de valores nulos
    non_null_count: Optional[int] = 0  # Conteo absoluto de valores válidos
    total_rows: Optional[int] = 0  # Total de filas analizadas


class VariableListResponse(BaseModel):
    """
    Respuesta paginada para el listado de variables.
    """
    items: List[Variable]
    total: int  # Total de variables que coinciden con el filtro
    page: int  # Página actual
    size: int  # Tamaño de página
    has_more: bool  # Indica si hay más páginas disponibles


class CompletenessItem(BaseModel):
    """
    Resumen de completitud para una variable específica.
    """
    variable: str
    valid_percentage: float
    null_count: int
    non_null_count: int
    total_rows: int
    dtype: str


class CompletenessResponse(BaseModel):
    """
    Respuesta paginada para métricas de completitud.
    """
    items: List[CompletenessItem]
    total: int
    page: int
    size: int
    has_more: bool


class StatsItem(BaseModel):
    """
    Ítem de estadística global por tipo de dato.
    """
    label: str  # Etiqueta visual (ej: "Numéricas")
    value: int  # Cantidad de variables de este tipo
    # Identificador interno del tipo (numeric, categorical, boolean, datetime)
    type: str


class StatsResponse(BaseModel):
    """
    Respuesta con estadísticas globales del dataset.
    """
    stats: List[StatsItem]


class DatasetInfoResponse(BaseModel):
    """
    Respuesta con información básica del dataset.
    """
    total_variables: int
    total_rows: int
    columns: List[str]


class DatasetStatsResponse(BaseModel):
    """

    Respuesta con estadísticas de completitud del dataset.
    """
    total_variables: int
    completeness: float  # Porcentaje de completitud promedio global


class CategoryStat(BaseModel):
    """
    Estadística para un valor específico de una variable categórica.
    """
    value: str
    label: Optional[str] = None
    count: int
    percentage: float


class CategoricalVariableStats(BaseModel):
    """
    Estadísticas detalladas para una variable categórica.
    """
    variable: str
    variable_label: Optional[str] = None
    total_rows: int
    top_values: List[CategoryStat]
    valid_percentage: Optional[float] = 0.0
    categories: Optional[List[Category]] = []


class CategoricalStatsResponse(BaseModel):
    """
    Respuesta paginada para estadísticas de variables categóricas.
    """
    items: List[CategoricalVariableStats]
    total: int
    page: int
    size: int
    has_more: bool
