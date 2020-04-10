import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from datetime import datetime, timedelta
import plotly.graph_objects as go

from bovespa_dashboard.connection.database import Postgres
from bovespa_dashboard.common.utils import load_file_json, database_result_to_named_tuple

configs_db = load_file_json("./configuration/database.json")
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

psql = Postgres(
        host=configs_db.get("HOST"),
        user=configs_db.get("USER"),
        password=configs_db.get("PASSWORD"),
        port=configs_db.get("PORT"),
        database=configs_db.get("DATABASE")
		)

cursor = psql.get_cursor
cursor.execute(
	"""
	SELECT tablename
	FROM pg_tables
	WHERE schemaname='stocks'
	"""
)

stocks = [s[0].upper() for s in cursor.fetchall()]
stocks.sort()

values_type_simple = [("Abertura", "open"), ("Fechamento", "close"),
	("Mínima", "low"),("Alta", "high"), ("Volume", "volume")]
values_type_computed = [("Diferença", "price_diff"), ("Retorno", "daily_return")]
values_all = values_type_simple + values_type_computed
values_all.sort()

app.layout = html.Div([
	
	html.Div([
		html.Div([
			html.Label('Período'),
			dcc.DatePickerRange(
				id='date-picker-range-historical',
				start_date=datetime.date(datetime.now()-timedelta(days=30)),
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
			html.Label('Valor'),
			dcc.Dropdown(
				id='stocks-price-type-historical',
				options=[
					{'label': v[0], 'value': v[1]} for v in values_all
				],
				value=values_type_simple[1][1]
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
			),
		], style={'width': '48%', 'display': 'inline-block'}),

		html.Div([
			html.Label('Gráfico'),
			dcc.Dropdown(
				id='stocks-selection-ohlc',
				options=[
					{'label': s, 'value': s} for s in ["Candlestick", "Ohlc"]
				],
				multi=False,
				value="Candlestick"
			)
		], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
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
	value_type_label = [l[0] for l in values_all if l[1] == value_type][0]
	fig = go.Figure()
	for stock in stocks:
		if value_type in [l[1] for l in values_type_simple]:
			query = \
				"""
				SELECT date, {value_type}
				FROM stocks.{stock}
				WHERE date >= '{start_date}'
					AND date <= '{end_date}'
					AND CLOSE NOTNULL
				"""
		else:
			query = \
				"""
				SELECT date, {value_type}
				FROM (
					SELECT *,
						(price_diff / close) AS daily_return
					FROM
					(SELECT *,
							(previous_close - close) AS price_diff
					FROM
						(SELECT *,
								LAG(close, 1) over() AS previous_close
						FROM
							(SELECT date, close
							FROM stocks.{stock}
							ORDER BY date) A
						WHERE 
							CLOSE NOTNULL ) B) C) D
				WHERE date >= '{start_date}'
					AND date <= '{end_date}'
				"""
		
		formatted = query.format(value_type=value_type, stock=stock.lower(), start_date=start_date, end_date=end_date)
		
		cursor.execute(formatted)
		result = database_result_to_named_tuple(cursor)

		if value_type in [l[1] for l in values_type_simple]:
			fig.add_trace(
				go.Scatter(
					x=result.date, y=getattr(result, value_type), 
					mode="lines", name=stock, connectgaps=False)
			)
		else:
			fig.add_trace(
				go.Waterfall(
					name=stock,
					x=result.date, y=getattr(result, value_type),

				)
			)
	return fig.update_layout(
		title=dict(
			text="Histórico de Valor ({label})".format(
				label=value_type_label.lower()) if value_type_label!='Volume' else "Histórico de Volume",
			x=0.5
		),
		plot_bgcolor="white",
		xaxis=dict(
			title="Data",
			type="category"
		),
		yaxis=dict(
			title="Valor"
		)
	)

@app.callback(
    Output('stocks-candle', 'figure'),
    [Input('stocks-selection-candle', 'value'), 
	Input('date-picker-range-candle', 'start_date'),
	Input('date-picker-range-candle', 'end_date'),
	Input('stocks-selection-ohlc', "value")])
def updade_stocks_candle(stock: str, start_date: str, end_date: str, chart_type: str):
	query = \
		"""
		SELECT date, low,
            	open,
            	close,
            	high
		FROM stocks.{stock}
		WHERE date >= '{start_date}'
			AND date <= '{end_date}'
			AND CLOSE NOTNULL
		"""
	formatted = query.format(stock=stock.lower(), start_date=start_date, end_date=end_date)
		
	cursor.execute(formatted)
	result = database_result_to_named_tuple(cursor)

	fig = go.Figure(
		getattr(go, chart_type)(
			x=result.date, low=result.low, 
			open=result.open, close=result.close, high=result.high
		)
	)

	return fig.update_layout(
		xaxis_rangeslider_visible=False,
		title=dict(
			text="Histórico de Variação ({stock})".format(stock=stock),
			x=0.5
		),
		plot_bgcolor="white",
		xaxis=dict(
			title="Data",
			type="category"
		),
		yaxis=dict(
			title="Variação"
		)
	
	)

if __name__ == '__main__':
    app.run_server(debug=True)