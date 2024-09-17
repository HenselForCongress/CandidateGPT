# mastermind/data_manager/load/__init__.py


import os

def load_data():
    """Load data from markdown files in the data directory."""
    data = {}
    base_dir = 'data'

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.md'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    key = os.path.relpath(path, base_dir)
                    data[key] = f.read()
    return data
