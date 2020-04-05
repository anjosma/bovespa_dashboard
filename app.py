import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd

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

psql.close()