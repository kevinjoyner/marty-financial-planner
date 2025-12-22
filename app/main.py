import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from .routers import scenarios, owners, accounts, projections, rules, transfers, financial_events, costs, income_sources, tax_limits, strategies
from .database import engine, Base

# Create tables (if not exist)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include Routers with explicit /api prefix
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(owners.router, prefix="/api", tags=["owners"])
app.include_router(accounts.router, prefix="/api", tags=["accounts"])
app.include_router(income_sources.router, prefix="/api", tags=["income_sources"])
app.include_router(costs.router, prefix="/api", tags=["costs"])
app.include_router(financial_events.router, prefix="/api", tags=["financial_events"])
app.include_router(transfers.router, prefix="/api", tags=["transfers"])
app.include_router(rules.router, prefix="/api", tags=["rules"])
app.include_router(tax_limits.router, prefix="/api", tags=["tax_limits"])
app.include_router(strategies.router, prefix="/api", tags=["strategies"]) # <--- NEW ROUTER
app.include_router(projections.router, prefix="/api", tags=["projections"])

# --- MOUNTS ---

# 1. Legacy Frontend (Optional)
if os.path.exists("frontend_legacy"):
    app.mount("/legacy", StaticFiles(directory="frontend_legacy", html=True), name="legacy")

# 2. Production Assets (The built JS/CSS from Vite)
if os.path.exists("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets", html=True), name="assets")

# 3. Main Entry Point
@app.get("/")
async def read_index():
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse('frontend/dist/index.html')
    return FileResponse('frontend/index.html')

# SPA Catch-all
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return FileResponse("frontend/index.html")
