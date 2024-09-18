# mastermind/data_manager/load/__init__.py
import os
from mastermind import logger

def load_data():
    """Load data from markdown files in the data directory."""
    logger.debug("📂 Starting data loading process. Ready for it?")
    data = {}
    base_dir = 'data'

    if not os.path.exists(base_dir):
        logger.error("❌ Data directory does not exist. We are never ever getting back together.")
        return data

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.md'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        key = os.path.relpath(path, base_dir)
                        data[key] = f.read()
                        logger.debug(f"📄 Loaded data from file: {path}. Look what you made me do!")
                except Exception as e:
                    logger.error(f"🚫 Error loading file: {path}. Error: {e}. You belong with me...or not.")

    if data:
        logger.info("📚 Data loaded successfully from markdown files. Everything has changed!")
    else:
        logger.warning("⚠️ No markdown files found or data is empty. I knew you were trouble.")

    return data
