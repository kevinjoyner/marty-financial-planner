from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import scenarios, owners, accounts, projections, rules, transfers, financial_events, costs, income_sources, tax_limits, strategies
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Financial Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(scenarios.router)
app.include_router(owners.router)
app.include_router(accounts.router)
app.include_router(projections.router)
app.include_router(rules.router)
app.include_router(transfers.router)
app.include_router(financial_events.router)
app.include_router(costs.router)
app.include_router(income_sources.router)
app.include_router(tax_limits.router)
app.include_router(strategies.router)

@app.get("/")
def read_root():
    return {"message": "Financial Planner API is running"}
