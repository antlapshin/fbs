import os
from dotenv import load_dotenv

load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required but not set")
    return value


TELEGRAM_BOT_TOKEN = _get_required_env("TELEGRAM_BOT_TOKEN")

admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_raw.split(",") if admin_id.strip()]

# Логирование для отладки (только если есть значение)
if admin_ids_raw:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔑 Loaded ADMIN_IDS: {ADMIN_IDS} from raw: '{admin_ids_raw}'")
else:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ ADMIN_IDS is empty or not set!")

MAGNIT_API_KEY = _get_required_env("MAGNIT_API_KEY")
OZON_API_KEY = _get_required_env("OZON_API_KEY")
OZON_CLIENT_ID = _get_required_env("OZON_CLIENT_ID")
WAREHOUSE_ID = _get_required_env("WAREHOUSE_ID")

MAGNIT_STOCKS_URL = "https://b2b-api.magnit.ru/api/seller/v1/products/sku/stocks"
MAGNIT_PRICES_URL = "https://b2b-api.magnit.ru/api/seller/v1/products/sku/price"
ORDERS_LIST_URL = "https://b2b-api.magnit.ru/api/seller/v1/orders/list/unprocessed"
PRODUCTS_URL = "https://b2b-api.magnit.ru/api/seller/v1/products/sku/list"
OZON_STOCKS_URL = "https://api-seller.ozon.ru/v4/product/info/stocks"
OZON_PRICES_URL = "https://api-seller.ozon.ru/v5/product/info/prices"

HEADERS = {
    "X-Api-Key": MAGNIT_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

HEADERS_OZON = {
    "Client-Id": OZON_CLIENT_ID,
    "Api-Key": OZON_API_KEY,
    "Content-Type": "application/json",
}