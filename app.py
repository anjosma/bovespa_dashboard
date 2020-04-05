import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

from bovespa_dashboard.connection.database import Postgres
from bovespa_dashboard.common.utils import load_file_json

configs_db = load_file_json("./configuration/database.json")
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

psql = Postgres(
        host=configs_db.get("HOST"),
        user=configs_db.get("USER"),
        password=configs_db.get("PASSWORD"),
        port=configs_db.get("PORT"),
        database=configs_db.get("DATABASE"))

cursor = psql.get_cursor
cursor.execute("select tablename from pg_tables where schemaname='stocks'")

stocks = [s[0].upper() for s in cursor.fetchall()]
stocks.sort()

app.layout = html.Div(
	children=[

        dcc.DatePickerRange(
        	id='date-picker-range',
            start_date=datetime.date(datetime.now()-timedelta(days=90)),
    		end_date=datetime.date(datetime.now())
		),

		dcc.Dropdown(
			id='stocks-selection',
    		options=[
        		{'label': s, 'value': s} for s in stocks
    		],
    		multi=True,
			value=["PETR3"]
		),

		dcc.Graph(id='stocks-historical')	

	]
)

@app.callback(
    Output('stocks-historical', 'figure'),
    [Input('stocks-selection', 'value'), 
	Input('date-picker-range', 'start_date'),
	Input('date-picker-range', 'end_date')])
def updade_stocks_historical(stocks: list, start_date: str, end_date: str):
	fig = go.Figure()
	for stock in stocks:
		query = "SELECT date, adj_close FROM stocks.{stock} \
			WHERE date >= '{start_date}' AND date <= '{end_date}' AND adj_close notnull"
		formatted = query.format(stock=stock.lower(), start_date=start_date, end_date=end_date)
		
		cursor.execute(formatted)
		results_stock = cursor.fetchall()
		
		dates = [t[0] for t in results_stock]
		values = [v[1] for v in results_stock]

		fig.add_trace(
			go.Scatter(x=dates, y=values, mode="lines", name=stock, connectgaps=False)
		)
	return fig.update_layout(
		title=dict(
			text="Histórico de Valor de Fechamento",
			x=0.5
		),
		plot_bgcolor="white",
		xaxis=dict(
			title="Data"
		),
		yaxis=dict(
			title="Valor"
		)
	)

if __name__ == '__main__':
    app.run_server(debug=True)