"""Updated main.py with DB initialization and all routes."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api.routes.exchange import router as exchange_router
from app.api.routes.balances import router as balances_router
from app.api.routes.finance import router as finance_router
from app.api.routes.entities import router as entities_router
from app.api.routes.budgets import router as budgets_router
from app.api.routes.upload import router as upload_router
from app.api.routes.retirement import router as retirement_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.accounts import router as accounts_router

app = FastAPI(title="Finance API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(exchange_router, prefix="/api")
app.include_router(balances_router, prefix="/api")
app.include_router(finance_router, prefix="/api")
app.include_router(entities_router, prefix="/api")
app.include_router(budgets_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(retirement_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(accounts_router, prefix="/api")
