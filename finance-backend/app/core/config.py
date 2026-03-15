import os
from pathlib import Path



DATASET_ROOT_PATH = str(Path(__file__).parent.parent.parent.parent / "dataset")

#DATASET_ROOT_PATH = str(Path.cwd().parent.parent.parent / "dataset")
os.makedirs(DATASET_ROOT_PATH, exist_ok=True)

API_KEY = "34cb491d8aea05377911d4c4"  # Sign up at https://exchangerate-api.com/
BASE_CURRENCY = "COP"
CURRENCIES = ["USD", "EUR", "COP", "GBP", "JPY", "CNY", "INR", "AUD", "CAD", "CHF"]