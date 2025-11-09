import requests
from config import *


def api_request(url, payload, operation_name):
    """Универсальная функция для API запросов"""
    try:
        headers = HEADERS if 'magnit' in url else HEADERS_OZON
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except Exception:
                return {"status": "success"}
        else:
            print(f"❌ {operation_name}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Ошибка {operation_name}: {e}")
        return None


def get_unprocessed_orders():
    """Получает список необработанных заказов"""
    payload = {"limit": 100, "offset": 0}
    data = api_request(ORDERS_LIST_URL, payload, "Получение заказов")
    return data.get('orders', []) if data else []


def get_all_products():
    """Получает все товары с названиями"""
    payload = {"limit": 1000}
    data = api_request(PRODUCTS_URL, payload, "Получение товаров")
    if not data:
        return {}

    products = data.get('result', [])
    product_mapping = {}
    for product in products:
        sku_id = str(product.get('sku_id'))
        seller_sku_id = product.get('seller_sku_id', 'N/A')
        title = product.get('title', 'N/A')
        product_mapping[sku_id] = {
            'seller_sku_id': seller_sku_id,
            'title': title
        }
    return product_mapping


def get_ozon_stocks():
    """Получает остатки с Ozon"""
    payload = {"filter": {"visibility": "ALL"}, "limit": 100}
    data = api_request(OZON_STOCKS_URL, payload, "Получение остатков Ozon")
    return data.get('items', []) if data else []


def get_ozon_prices():
    """Получает цены с Ozon"""
    payload = {"filter": {"visibility": "ALL"}, "limit": 100}
    data = api_request(OZON_PRICES_URL, payload, "Получение цен Ozon")
    return data.get('items', []) if data else []


def sync_stocks_with_magnit():
    """Синхронизирует остатки с Magnit"""
    stock_items = get_ozon_stocks()
    if not stock_items:
        return False, "Нет данных по остаткам с Ozon"

    magnit_stocks = []
    for item in stock_items:
        offer_id = item.get('offer_id')
        if not offer_id:
            continue
        stocks = item.get('stocks', [])
        present = sum(stock.get('present', 0) for stock in stocks)
        magnit_stocks.append({
            "seller_sku_id": offer_id,
            "stock": present,
            "warehouse_id": WAREHOUSE_ID
        })

    if not magnit_stocks:
        return False, "Нет данных по остаткам для отправки"

    payload = {"stocks": magnit_stocks}
    result = api_request(MAGNIT_STOCKS_URL, payload, "Отправка остатков")
    return bool(result), "Остатки успешно синхронизированы" if result else "Ошибка синхронизации остатков"


def sync_prices_with_magnit():
    """Синхронизирует цены с Magnit"""
    price_items = get_ozon_prices()
    if not price_items:
        return False, "Нет данных по ценам с Ozon"

    magnit_prices = []
    for item in price_items:
        offer_id = item.get('offer_id')
        if not offer_id:
            continue
        price_info = item.get('price', {})
        price = price_info.get('price')
        if price is not None:
            try:
                if isinstance(price, str):
                    price_value = float(price.replace('₽', '').replace(' ', '').strip())
                else:
                    price_value = float(price)
                magnit_prices.append({
                    "seller_sku_id": offer_id,
                    "price": price_value,
                    "currency_code": "RUB"
                })
            except (ValueError, TypeError):
                continue

    if not magnit_prices:
        return False, "Нет данных по ценам для отправки"

    payload = {"prices": magnit_prices}
    result = api_request(MAGNIT_PRICES_URL, payload, "Отправка цен в Magnit")
    return bool(result), "Цены успешно синхронизированы" if result else "Ошибка синхронизации цен"


def update_single_stock(seller_sku_id, new_stock):
    """Обновляет остаток одного товара"""
    payload = {
        "stocks": [{
            "seller_sku_id": seller_sku_id,
            "stock": new_stock,
            "warehouse_id": WAREHOUSE_ID
        }]
    }
    result = api_request(MAGNIT_STOCKS_URL, payload, f"Обновление остатка {seller_sku_id}")
    return bool(
        result), f"Остаток {seller_sku_id} обновлен: {new_stock} шт" if result else f"Ошибка обновления остатка {seller_sku_id}"


def update_single_price(seller_sku_id, new_price):
    """Обновляет цену одного товара"""
    payload = {
        "prices": [{
            "seller_sku_id": seller_sku_id,
            "price": new_price,
            "currency_code": "RUB"
        }]
    }
    result = api_request(MAGNIT_PRICES_URL, payload, f"Обновление цены {seller_sku_id}")
    return bool(
        result), f"Цена {seller_sku_id} обновлена: {new_price} руб" if result else f"Ошибка обновления цены {seller_sku_id}"

def get_stocks_info():
    """Получает информацию об остатках товаров из Magnit"""
    print("📊 Получаем информацию об остатках...")
    products = get_all_products()
    if not products:
        return {}

    sku_ids = list(products.keys())
    payload = {
        "filter": {"sku_ids": [int(i) for i in sku_ids]},
        "pagination": {"dir": "DESC", "page": 0, "page_size": len(sku_ids)}
    }

    STOCKS_INFO_URL = "https://b2b-api.magnit.ru/api/seller/v1/products/sku/stocks/info"
    data = api_request(STOCKS_INFO_URL, payload, "Получение остатков")
    if not data:
        return {}

    result = {}
    for item in data.get("result", []):
        for stock in item.get("stock_info_details", []):
            if stock["type"] == "FBS":
                result[str(item["sku_id"])] = {
                    "stock": stock["stock"],
                    "reserved": stock["reserved"]
                }

    print(f"✅ Получены остатки для {len(result)} товаров")
    return result

def get_prices_info():
    """Получает информацию о ценах товаров из Magnit"""
    print("💰 Получаем информацию о ценах...")
    products = get_all_products()
    if not products:
        return {}

    # Собираем seller_sku_ids всех товаров
    seller_sku_ids = [product_info.get('seller_sku_id') for product_info in products.values()]
    seller_sku_ids = [sku for sku in seller_sku_ids if sku and sku != 'N/A']

    if not seller_sku_ids:
        print("❌ Не найдено seller_sku_ids для получения цен")
        return {}

    # Формируем payload для запроса цен
    payload = {
        "filter": {
            "seller_sku_ids": seller_sku_ids
        },
        "pagination": {
            "dir": "DESC",
            "page": 0,
            "page_size": len(seller_sku_ids)
        }
    }

    MAGNIT_PRICES_INFO_URL = "https://b2b-api.magnit.ru/api/seller/v1/products/sku/price/info"
    data = api_request(MAGNIT_PRICES_INFO_URL, payload, "Получение текущих цен из Magnit")
    if not data:
        return {}

    prices_info = {}
    items = data.get('result', [])

    for item in items:
        seller_sku_id = item.get('seller_sku_id')
        price = item.get('price', 0)

        if seller_sku_id and price is not None:
            try:
                price_value = float(price)
                prices_info[seller_sku_id] = price_value
            except (ValueError, TypeError):
                prices_info[seller_sku_id] = 0

    print(f"✅ Получены цены для {len(prices_info)} товаров")
    return prices_info