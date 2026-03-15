from fastapi import APIRouter
from datetime import date
import yfinance as yf



router = APIRouter(tags=["Exchange"])

@router.get("/exchange-rate")
def get_exchange_rate():
    """
    Obtiene la tasa de cambio COP → USD correspondiente al día actual.

    La tasa se obtiene desde Yahoo Finance utilizando el ticker `COPUSD=X`,
    que representa el valor del peso colombiano (COP) frente al dólar estadounidense (USD).

    Proceso:
    1. Se consulta el historial del día actual.
    2. Se toma el último valor de cierre (Close).
    3. Se calcula la tasa COP → USD (invirtiendo el valor).
    4. Se redondea a dos decimales para uso financiero.

    Retorna:
        dict: Información de la tasa de cambio con la siguiente estructura:
        {
            "date": "YYYY-MM-DD",
            "rate": float,   # Tasa COP → USD
            "base": "COP",
            "target": "USD"
        }
    """
    pair = yf.Ticker("COPUSD=X")
    data = pair.history(period="1d")
    rate_today = data["Close"][-1]

    print("Tipo de cambio COP→USD:", round(rate_today,2))
    return {
        "date": date.today().isoformat(),
        "rate": round(1/rate_today,2),
        "base": "COP",
        "target": "USD"
    }
