from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth_router,
    workspaces_router,
    tags_router,
    tasks_router,
    analytics_router,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(workspaces_router, prefix="/api")
app.include_router(tags_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


@app.get("/", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok", "message": "Time Management API is running"}
