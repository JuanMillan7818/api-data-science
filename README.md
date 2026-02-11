# API Data Science - Backend

Este proyecto es el backend para el Dashboard de Ciencia de Datos, desarrollado con **FastAPI**. Proporciona endpoints para consultar variables, estadísticas de completitud y datos generales del dataset de "Centenarios".

## Tecnologías Principales

-   **Python 3.12+**
-   **FastAPI:** Framework web moderno y rápido para construir APIs.
-   **Pandas:** Procesamiento y análisis de datos (lectura de Excel).
-   **Uvicorn:** Servidor ASGI para producción y desarrollo.
-   **Pydantic:** Validación de datos y gestión de esquemas.

## Estructura del Proyecto

```
api_python/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── graph/       # Rutas principales (router.py)
│   │       └── utils/       # Utilidades auxiliares
│   ├── schemas/             # Modelos Pydantic (info_variables.py)
│   ├── services/            # Lógica de negocio (centenarios.py)
│   └── main.py              # Punto de entrada de la aplicación
├── centenarios/             # Archivos de datos (Excel)
│   ├── centenarios_diccionario.xlsx
│   └── centenarios_metabolomica.xlsx
├── requirements.txt         # Dependencias del proyecto
└── requirements.in          # Entrada para pip-compile
```

## Configuración y Ejecución

### 1. Crear entorno virtual (Opcional pero recomendado)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar el servidor de desarrollo

```bash
uvicorn app.main:app --reload
```

El servidor iniciará en `http://127.0.0.1:8000`.

## Documentación de la API

FastAPI genera automáticamente documentación interactiva. Una vez iniciado el servidor, puedes visitarla en:

-   **Swagger UI:** `http://127.0.0.1:8000/docs`
-   **ReDoc:** `http://127.0.0.1:8000/redoc`

## Endpoints Principales

-   `GET /api/v1/graph/variables`: Lista paginada de variables con búsqueda.
-   `GET /api/v1/graph/completeness`: Estadísticas de completitud (nulos/válidos) por variable.
-   `GET /api/v1/graph/stats`: Resumen global del dataset.
