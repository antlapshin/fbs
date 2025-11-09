import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []

# Magnit API
MAGNIT_API_KEY = os.getenv('MAGNIT_API_KEY', "13c736b0-29b1-4030-b479-cd5a2e875481")
OZON_API_KEY = os.getenv('OZON_API_KEY', "de1d6c24-b14e-412d-8b90-42d9328c72a1")
OZON_CLIENT_ID = os.getenv('OZON_CLIENT_ID', "1127243")
WAREHOUSE_ID = os.getenv('WAREHOUSE_ID', "2e8fa736-c054-44e6-82b3-9a03dc9ae5a6")

# API URLs (используем основные из вашего кода)
MAGNIT_STOCKS_URL = "https://b2b-api.magnit.ru/api/seller/v1/products/sku/stocks"
MAGNIT_PRICES_URL = "https://b2b-api.magnit.ru/api/seller/v1/products/sku/price"
ORDERS_LIST_URL = "https://b2b-api.magnit.ru/api/seller/v1/orders/list/unprocessed"
PRODUCTS_URL = "https://b2b-api.magnit.ru/api/seller/v1/products/sku/list"
OZON_STOCKS_URL = "https://api-seller.ozon.ru/v4/product/info/stocks"
OZON_PRICES_URL = "https://api-seller.ozon.ru/v5/product/info/prices"

HEADERS = {
    "X-Api-Key": MAGNIT_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

HEADERS_OZON = {
    "Client-Id": OZON_CLIENT_ID,
    "Api-Key": OZON_API_KEY,
    "Content-Type": "application/json"
}