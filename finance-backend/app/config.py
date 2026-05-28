import os
from pathlib import Path


# DATASET_ROOT_PATH: can be overridden via environment variable (Docker)
DATASET_ROOT_PATH = os.environ.get(
    "DATASET_ROOT_PATH",
    str(Path(__file__).parent.parent.parent.parent / "dataset")
)
os.makedirs(DATASET_ROOT_PATH, exist_ok=True)

API_KEY = os.environ.get("EXCHANGERATE_API_KEY", "34cb491d8aea05377911d4c4")
BASE_CURRENCY = "COP"
CURRENCIES = ["USD", "EUR", "COP", "GBP", "JPY", "CNY", "INR", "AUD", "CAD", "CHF"]