from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from .database import engine, Base
from .routers import scenarios, items, history, strategies, projections

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Marty Finance Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(items.router, prefix="/api", tags=["items"])
app.include_router(history.router, prefix="/api", tags=["history"])
app.include_router(strategies.router, prefix="/api", tags=["strategies"])
app.include_router(projections.router, prefix="/api", tags=["projections"])

# Static Files (Frontend)
if os.path.isdir("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            return {"error": "API route not found"}
        return FileResponse("frontend/dist/index.html")

@app.get("/")
def read_root():
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return {"message": "Marty Finance Engine API is running. Frontend not built."}
