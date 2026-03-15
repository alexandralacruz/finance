from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.exchange import router as exchange_router
from app.api.routes.balances import router as balances_router
from app.api.routes.finance import router as finance_router

app = FastAPI(title="Finance API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exchange_router, prefix="/api")
app.include_router(balances_router, prefix="/api")
app.include_router(finance_router, prefix="/api")