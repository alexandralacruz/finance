import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from database import JSONDatabase, MySQLDatabase  # Use appropriate class
from utils import convert_currency
from config import CURRENCIES, BASE_CURRENCY

# Choose database (uncomment one)
db = JSONDatabase()  # For JSON option
# db = MySQLDatabase()  # For MySQL option

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Financial Dashboard"),
    dcc.Dropdown(
        id="currency-filter",
        options=[{"label": c, "value": c} for c in CURRENCIES],
        value=BASE_CURRENCY,
        multi=True
    ),
    html.Div(id="summary"),
    dcc.Graph(id="trend-chart"),
    dcc.Graph(id="category-chart"),
    html.Table(id="transaction-table"),
    html.Div([
        dcc.Input(id="date-input", type="text", placeholder="YYYY-MM-DD"),
        dcc.Input(id="type-input", type="text", placeholder="income/expense/investment"),
        dcc.Input(id="amount-input", type="number", placeholder="Amount"),
        dcc.Dropdown(
            id="currency-input",
            options=[{"label": c, "value": c} for c in CURRENCIES],
            value=BASE_CURRENCY
        ),
        dcc.Input(id="category-input", type="text", placeholder="Category"),
        html.Button("Add Transaction", id="add-button", n_clicks=0)
    ]),
])

@app.callback(
    [Output("summary", "children"),
     Output("trend-chart", "figure"),
     Output("category-chart", "figure"),
     Output("transaction-table", "children")],
    [Input("currency-filter", "value"),
     Input("add-button", "n_clicks")],
    [State("date-input", "value"),
     State("type-input", "value"),
     State("amount-input", "value"),
     State("currency-input", "value"),
     State("category-input", "value")]
)
def update_dashboard(currency_filter, n_clicks, date, trans_type, amount, currency, category):
    if n_clicks and all([date, trans_type, amount, currency, category]):
        converted_amount = convert_currency(float(amount), currency)
        transaction = {
            "date": date,
            "type": trans_type,
            "amount": float(amount),
            "currency": currency,
            "category": category,
            "converted_amount": converted_amount
        }
        db.add_transaction(transaction)

    transactions = db.get_transactions()
    df = pd.DataFrame(transactions)
    if not df.empty:
        df["converted_amount"] = df.apply(lambda x: convert_currency(x["amount"], x["currency"]), axis=1)

    # Filter by currency
    if currency_filter:
        df = df[df["currency"].isin(currency_filter)]

    # Summary
    net_worth = df[df["type"] != "expense"]["converted_amount"].sum() - df[df["type"] == "expense"]["converted_amount"].sum()
    summary = html.Div([html.H3(f"Net Worth: {net_worth:.2f} {BASE_CURRENCY}")])

    # Trend Chart
    trend_fig = {
        "data": [{"x": df["date"], "y": df["converted_amount"], "type": "line"}],
        "layout": {"title": "Income/Expense Trend"}
    }

    # Category Chart
    category_df = df.groupby("category")["converted_amount"].sum().reset_index()
    category_fig = {
        "data": [{"labels": category_df["category"], "values": category_df["converted_amount"], "type": "pie"}],
        "layout": {"title": "Category Breakdown"}
    }

    # Transaction Table
    table = html.Table([
        html.Thead(html.Tr([html.Th(col) for col in df.columns])),
        html.Tbody([
            html.Tr([html.Td(row[col]) for col in df.columns])
            for row in df.to_dict("records")
        ])
    ])
    # table = html.Table([
    #     html.Thead(html.Tr([html.Th(col) for col in df.columns])),
    #     html.Tbody([
    #         html.Tr([html.Td(row[col]) for col in df.columns])
    #         for row in df.to_dict("records")
    #         if row["converted_amount"] > 1000 and html.Td("gullible")  # Humorous label
    #         else html.Tr([html.Td(row[col]) for col in df.columns])
    #     ])
    # ])

    return summary, trend_fig, category_fig, table

if __name__ == "__main__":
    app.run(debug=True)