import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

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

values_type = [("Abertura", "open"), ("Fechamento", "close"), ("Mínima", "low"), ("Alta", "high"), ("Volume", "volume")]

nav_menu = html.Div([
    html.Ul([
            html.Li([
                    dcc.Link('Page A', href='/page-a')
                    ], className=''),
            html.Li([
                    dcc.Link('Page B', href='/page-b')
                    ], className=''),
            ], className='nav navbar-nav')
], className='navbar navbar-default navbar-static-top')

app.layout = html.Div([
	
	html.Div([
		html.Div([
			html.Label('Período'),
			dcc.DatePickerRange(
				id='date-picker-range-historical',
				start_date=datetime.date(datetime.now()-timedelta(days=30*6)),
				end_date=datetime.date(datetime.now()),
				display_format="D/M/Y"
			),

			html.Label('Ações'),
			dcc.Dropdown(
				id='stocks-selection-historical',
				options=[
					{'label': s, 'value': s} for s in stocks
				],
				multi=True,
				value=["PETR3", "MGLU3"]
			)
		], style={'width': '48%', 'display': 'inline-block'}),
	
		html.Div([
			html.Label('Preço'),
			dcc.Dropdown(
				id='stocks-price-type-historical',
				options=[
					{'label': v[0], 'value': v[1]} for v in values_type
				],
				value=values_type[1][1]
			),
		], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
	]),

	dcc.Graph(id='stocks-historical'),

	html.Div([
		html.Div([
			html.Label('Período'),
			dcc.DatePickerRange(
				id='date-picker-range-candle',
				start_date=datetime.date(datetime.now()-timedelta(days=30)),
				end_date=datetime.date(datetime.now()),
				display_format="D/M/Y"
			),

			html.Label('Ação'),
			dcc.Dropdown(
				id='stocks-selection-candle',
				options=[
					{'label': s, 'value': s} for s in stocks
				],
				multi=False,
				value="PETR3"
			)
		], style={'width': '48%', 'display': 'inline-block'}),
	]),

	dcc.Graph(id='stocks-candle'),
])

@app.callback(
    Output('stocks-historical', 'figure'),
    [Input('stocks-selection-historical', 'value'), 
	Input('date-picker-range-historical', 'start_date'),
	Input('date-picker-range-historical', 'end_date'),
	Input('stocks-price-type-historical', 'value')])
def updade_stocks_historical(stocks: list, start_date: str, end_date: str, value_type: str):
	value_type_label = [l[0] for l in values_type if l[1] == value_type][0]
	fig = go.Figure()
	for stock in stocks:
		query = "SELECT date, {value_type} FROM stocks.{stock} \
			WHERE date >= '{start_date}' AND date <= '{end_date}' AND close notnull"
		formatted = query.format(value_type=value_type, stock=stock.lower(), start_date=start_date, end_date=end_date)
		
		cursor.execute(formatted)
		results_stock = cursor.fetchall()
		
		dates = [t[0] for t in results_stock]
		values = [v[1] for v in results_stock]

		fig.add_trace(
			go.Scatter(x=dates, y=values, mode="lines", name=stock, connectgaps=False)
		)
	return fig.update_layout(
		title=dict(
			text="Histórico de Valor ({label})".format(
				label=value_type_label.lower()) if value_type_label!='Volume' else "Histórico de Volume",
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

@app.callback(
    Output('stocks-candle', 'figure'),
    [Input('stocks-selection-candle', 'value'), 
	Input('date-picker-range-candle', 'start_date'),
	Input('date-picker-range-candle', 'end_date')])
def updade_stocks_candle(stock: str, start_date: str, end_date: str):
	query = "SELECT date, low, open, close, high FROM stocks.{stock} \
			WHERE date >= '{start_date}' AND date <= '{end_date}' AND close notnull"
	formatted = query.format(stock=stock.lower(), start_date=start_date, end_date=end_date)
		
	cursor.execute(formatted)
	results_stock = cursor.fetchall()
		
	dates = [t[0] for t in results_stock]
	low = [v[1] for v in results_stock]
	open = [v[2] for v in results_stock]
	close = [v[3] for v in results_stock]
	high = [v[4] for v in results_stock]

	return go.Figure(
		go.Candlestick(
			x=dates, low=low, open=open, close=close, high=high
		)
	).update_layout(
		xaxis_rangeslider_visible=False,
		title=dict(
			text="Histórico de Variação ({stock})".format(stock=stock),
			x=0.5
		),
		plot_bgcolor="white",
		xaxis=dict(
			title="Data"
		),
		yaxis=dict(
			title="Variação"
		)
	
	)

if __name__ == '__main__':
    app.run_server(debug=True)