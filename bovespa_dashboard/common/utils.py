import json
import os
from datetime import datetime

def load_file_json(file_name: str) -> dict:
    with open(file_name, 'r') as json_file:
        return json.load(json_file)

def create_dir(file_path: str) -> None:
    path = os.path.dirname(file_path)
    if not os.path.exists(path):
        os.makedirs(path)
