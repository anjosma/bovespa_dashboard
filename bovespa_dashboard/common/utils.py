import json
import os
from datetime import datetime
import collections

def load_file_json(file_name: str) -> dict:
    with open(file_name, 'r') as json_file:
        return json.load(json_file)

def create_dir(file_path: str) -> None:
    path = os.path.dirname(file_path)
    if not os.path.exists(path):
        os.makedirs(path)

def database_result_to_named_tuple(cursor):
    columns = [desc[0] for desc in cursor.description]
    results_stock = cursor.fetchall()
    stock_values={}
    for i, column in enumerate(columns):
        stock_values[column] = [t[i] for t in results_stock]
    named_tuple = collections.namedtuple("results", sorted(stock_values))
    return named_tuple(**stock_values)