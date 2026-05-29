from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

from app.routers import (
    auth_router,
    workspaces_router,
    tags_router,
    tasks_router,
    analytics_router,
    parser_router,
)

app = FastAPI()

load_dotenv()

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
app.include_router(parser_router, prefix="/api")


@app.get("/")
def root() -> dict:
    return {"status": "ok", "message": "Time Management API is running"}


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok", "message": "Time Management API is running"}
