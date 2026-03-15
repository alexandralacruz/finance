from fastapi import APIRouter

router = APIRouter(tags=["Balances"])

@router.get("/balances")
def get_balances():
    return [
        {
            "entity": "BC",
            "currency": "COP",
            "balance": 12500000
        },
        {
            "entity": "Payoneer",
            "currency": "USD",
            "balance": 3200
        },
        {
            "entity": "Amerant",
            "currency": "USD",
            "balance": 1850
        }
    ]
