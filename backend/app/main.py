from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.battle_routes import router as battle_router
from app.routes.data_routes import router as data_router
from app.routes.health_routes import router as health_router
from app.routes.type_routes import router as type_router

app = FastAPI(title="Pokemon Decision Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(type_router)
app.include_router(battle_router)
app.include_router(data_router)