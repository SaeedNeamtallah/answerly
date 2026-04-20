# from dotenv import dotenv_values
# config = dotenv_values(".env")

# # Flower configuration
# port = 5555
# max_tasks = 10000
# # db = 'flower.db'  # SQLite database for persistent storage
# auto_refresh = True

# # Authentication (optional)
# basic_auth = [f'admin:{config["CELERY_FLOWER_PASSWORD"]}']

from dotenv import dotenv_values
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
config = dotenv_values(ROOT_DIR / ".env")

port = 5555
max_tasks = 10000
auto_refresh = True

basic_auth = [f'admin:{config.get("CELERY_FLOWER_PASSWORD", "")}']
