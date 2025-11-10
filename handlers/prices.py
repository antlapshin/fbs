from telegram import Update
from telegram.ext import ContextTypes
from magnit_api import sync_prices_with_magnit, get_all_products, update_single_price, get_prices_info
from keyboards import get_prices_keyboard, get_back_keyboard


async def show_prices_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню управления ценами"""
    await update.message.reply_text(
        "💰 Управление ценами\n\n"
        "Выберите действие:",
        reply_markup=get_prices_keyboard()
    )


async def sync_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Синхронизирует цены"""
    await update.message.reply_text("🔄 Синхронизирую цены...")

    success, message = sync_prices_with_magnit()

    if success:
        await update.message.reply_text(f"✅ {message}")
    else:
        await update.message.reply_text(f"❌ {message}")


async def start_price_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс редактирования цены"""
    products = get_all_products()
    if not products:
        await update.message.reply_text("❌ Не удалось получить список товаров")
        return

    context.user_data['products'] = products
    context.user_data['state'] = 'waiting_price_product'

    message = "💰 Выберите товар для редактирования цены:\n\n"

    sorted_products = sorted(
        products.items(),
        key=lambda x: x[1].get('seller_sku_id', 'N/A')
    )

    for i, (sku_id, product_info) in enumerate(sorted_products, 1):
        seller_sku = product_info.get('seller_sku_id', 'N/A')
        title = product_info.get('title', 'N/A')
        message += f"{i}. {seller_sku} - {title}\n"

    message += "\nВведите номер товара:"

    await update.message.reply_text(message, reply_markup=get_back_keyboard())


async def handle_price_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор товара для редактирования цены"""
    try:
        product_num = int(update.message.text.strip())
        products = context.user_data.get('products', {})

        if not products:
            await update.message.reply_text("❌ Ошибка: данные о товарах утеряны")
            context.user_data.pop('state', None)
            return

        sorted_products = sorted(
            products.items(),
            key=lambda x: x[1].get('seller_sku_id', 'N/A')
        )

        if 1 <= product_num <= len(sorted_products):
            selected_product = sorted_products[product_num - 1]
            seller_sku = selected_product[1].get('seller_sku_id')
            title = selected_product[1].get('title')

            context.user_data['selected_product'] = seller_sku
            context.user_data['selected_title'] = title
            context.user_data['state'] = 'waiting_price_value'

            await update.message.reply_text(
                f"✏️ Редактирование цены: {seller_sku}\n"
                f"📝 Название: {title}\n\n"
                f"Введите новую цену (руб):"
            )
        else:
            await update.message.reply_text("❌ Неверный номер товара")

    except ValueError:
        await update.message.reply_text("❌ Введите число")


async def handle_price_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод нового значения цены"""
    try:
        new_price = float(update.message.text.strip())
        seller_sku = context.user_data.get('selected_product')
        title = context.user_data.get('selected_title')

        if new_price < 0:
            await update.message.reply_text("❌ Цена не может быть отрицательной")
            return

        await update.message.reply_text(f"🔄 Обновляю цену {seller_sku}...")

        success, message = update_single_price(seller_sku, new_price)

        if success:
            await update.message.reply_text(f"✅ {message}")
        else:
            await update.message.reply_text(f"❌ {message}")

        # Сбрасываем состояние
        context.user_data.pop('state', None)
        context.user_data.pop('selected_product', None)
        context.user_data.pop('selected_title', None)
        context.user_data.pop('products', None)

        # Возвращаем в меню цен
        await update.message.reply_text(
            "💰 Управление ценами\n\nВыберите действие:",
            reply_markup=get_prices_keyboard()
        )

    except ValueError:
        await update.message.reply_text("❌ Введите число")


async def show_current_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущие цены товаров"""
    await update.message.reply_text("💰 Получаю информацию о ценах...")

    try:
        # Получаем товары и цены
        products = get_all_products()
        prices_info = get_prices_info()  # Нужно добавить эту функцию в magnit_api.py

        if not products:
            await update.message.reply_text("❌ Не удалось получить список товаров")
            return

        message = "💰 ТЕКУЩИЕ ЦЕНЫ:\n\n"

        sorted_products = sorted(
            products.items(),
            key=lambda x: x[1].get('seller_sku_id', 'N/A')
        )

        for i, (sku_id, product_info) in enumerate(sorted_products[:10], 1):
            seller_sku = product_info.get('seller_sku_id', 'N/A')
            title = product_info.get('title', 'N/A')
            price = prices_info.get(seller_sku, 0)

            message += f"{i}. {seller_sku} - {title}\n"
            message += f"   💰 Цена: {price:.2f} руб\n\n"

        if len(sorted_products) > 10:
            message += f"... и еще {len(sorted_products) - 10} товаров"

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении цен: {str(e)}")