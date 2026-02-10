from typing import List, Optional, Any
from pydantic import BaseModel


class Category(BaseModel):
    code: str
    value: str


class Variable(BaseModel):
    variable: str
    variable_label: Optional[str] = None
    dtype: Optional[str] = "unknown"
    categories: Optional[List[Category]] = []
    keywords: Optional[List[str]] = []


class VariableListResponse(BaseModel):
    items: List[Variable]
    total: int
    page: int
    size: int
    has_more: bool


class CompletenessItem(BaseModel):
    variable: str
    valid_percentage: float
    null_count: int
    non_null_count: int
    total_rows: int
    dtype: str


class CompletenessResponse(BaseModel):
    items: List[CompletenessItem]


class StatsItem(BaseModel):
    label: str
    value: int
    type: str  # numeric, categorical, boolean, datetime


class StatsResponse(BaseModel):
    stats: List[StatsItem]
    total_variables: int
    completeness: float
