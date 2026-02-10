from app.api.v1.graph import router as graph_router
from fastapi import FastAPI
from app.api.v1.utils import variables    # Importa las rutas
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API DATA SCIENCE", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Permitir que soliciten datos desde cueal origen (cual web o dispositivo)
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# .... REGISTRA LAS RUTAS
app.include_router(variables.router, prefix="/api/v1")
app.include_router(graph_router.router, prefix="/api/v1/graph", tags=["Graph"])
