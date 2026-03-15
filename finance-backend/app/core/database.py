import json
from pathlib import Path
import pymysql
from config import BASE_CURRENCY

class JSONDatabase:
    def __init__(self, filepath="data/transactions.json"):
        self.filepath = Path(filepath)
        self.data = self.load_data()

    def load_data(self):
        if self.filepath.exists():
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {"transactions": []}

    def save_data(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=4)

    def add_transaction(self, transaction):
        self.data["transactions"].append(transaction)
        self.save_data()

    def get_transactions(self):
        return self.data["transactions"]


class MySQLDatabase:
    def __init__(self, host="localhost", user="root", password="password", database="finance"):
        self.conn = pymysql.connect(
            host=host, user=user, password=password, database=database
        )
        self.create_table()

    def create_table(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATETIME,
                    type ENUM('income', 'expense', 'investment'),
                    amount DECIMAL(10, 2),
                    currency VARCHAR(3),
                    category VARCHAR(50),
                    converted_amount DECIMAL(10, 2)
                )
            """)
            self.conn.commit()

    def add_transaction(self, transaction):
        with self.conn.cursor() as cursor:
            sql = """
                INSERT INTO transactions (date, type, amount, currency, category, converted_amount)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                transaction["date"],
                transaction["type"],
                transaction["amount"],
                transaction["currency"],
                transaction["category"],
                transaction.get("converted_amount", 0)
            ))
            self.conn.commit()

    def get_transactions(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM transactions")
            return cursor.fetchall()

    def __del__(self):
        self.conn.close()