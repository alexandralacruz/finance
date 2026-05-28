"""Exchange rate routes with multi-currency support via exchangerate-api.com."""
import logging
from datetime import date

import requests
import yfinance as yf
from fastapi import APIRouter, HTTPException

from app.config import API_KEY, BASE_CURRENCY

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Exchange"])

# Supported currencies
SUPPORTED_CURRENCIES = ["USD", "EUR", "COP", "GBP", "JPY", "CNY", "INR", "AUD", "CAD", "CHF", "MXN", "BRL", "ARS"]


@router.get("/exchange-rate")
def get_exchange_rate(target: str = "USD"):
    """
    Get COP → target exchange rate.
    Uses exchangerate-api.com as primary source, yfinance as fallback.
    """
    logger.info(f"----- Fetching exchange rate: COP → {target}-----")
    # Primary: exchangerate-api
    try:
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/COP"
        resp = requests.get(url, timeout=10)
        data = resp.json()

        if data.get("result") == "success":
            logger.info("Successfully fetched exchange rate from exchangerate-api")
            rates = data.get("conversion_rates", {})
            if target in rates:
                return {
                    "date": date.today().isoformat(),
                    "rate": round(rates[target], 6),
                    "base": "COP",
                    "target": target,
                }
    except Exception:
        pass

    # Fallback: yfinance
    try:
        pair = yf.Ticker(f"COP{target}=X")
        hist = pair.history(period="1d")
        if hist is not None and not hist.empty:
            logger.info("exchangerate-api fail but Successfully fetched exchange rate from yfinance")
            rate_today = hist["Close"].iloc[-1]
            return {
                "date": date.today().isoformat(),
                "rate": round(float(rate_today), 6),
                "base": "COP",
                "target": target,
            }
    except Exception:
        pass

    raise HTTPException(status_code=500, detail="Could not fetch exchange rate")


@router.get("/exchange-rates")
def get_all_exchange_rates():
    """Get all supported exchange rates from COP."""
    try:
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/COP"
        resp = requests.get(url, timeout=10)
        data = resp.json()

        if data.get("result") == "success":
            all_rates = data.get("conversion_rates", {})
            rates = {
                curr: round(all_rates[curr], 6)
                for curr in SUPPORTED_CURRENCIES
                if curr in all_rates and curr != "COP"
            }
            return {
                "date": date.today().isoformat(),
                "base": "COP",
                "rates": rates,
            }

        raise HTTPException(status_code=500, detail="API error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-rate/{from_currency}/{to_currency}")
def get_pair_rate(from_currency: str, to_currency: str):
    """Get exchange rate between any two currencies."""
    try:
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{from_currency.upper()}"
        resp = requests.get(url, timeout=10)
        data = resp.json()

        if data.get("result") == "success":
            rates = data.get("conversion_rates", {})
            if to_currency.upper() in rates:
                return {
                    "date": date.today().isoformat(),
                    "rate": round(rates[to_currency.upper()], 6),
                    "base": from_currency.upper(),
                    "target": to_currency.upper(),
                }

        raise HTTPException(status_code=404, detail=f"Rate not found: {from_currency}→{to_currency}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
