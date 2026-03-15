import requests
import json
from app.core.config import API_KEY, BASE_CURRENCY

def get_exchange_rate(from_currency):
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{from_currency}"
    response = requests.get(url)
    data = response.json()
    return data["conversion_rates"][BASE_CURRENCY]

def convert_currency(amount, from_currency):
    rate = get_exchange_rate(from_currency)
    return amount * rate