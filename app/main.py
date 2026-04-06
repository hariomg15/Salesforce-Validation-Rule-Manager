from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health
from app.api.routes import validation_rules
from app.core.config import settings
from app.db.init_db import init_db


app = FastAPI(
    title="Salesforce Validation Rule Switch API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(validation_rules.router, prefix="/api/validation-rules", tags=["validation-rules"])


@app.on_event("startup")
def on_startup() -> None:
    init_db()
