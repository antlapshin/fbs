from telegram import Update
from telegram.ext import ContextTypes
from magnit_api import sync_stocks_with_magnit, get_all_products, update_single_stock, get_stocks_info
from keyboards import get_stocks_keyboard, get_back_keyboard


async def show_stocks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню управления остатками"""
    await update.message.reply_text(
        "📊 Управление остатками\n\n"
        "Выберите действие:",
        reply_markup=get_stocks_keyboard()
    )


async def show_current_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущие остатки товаров"""
    await update.message.reply_text("📊 Получаю информацию об остатках...")

    try:
        # Получаем товары и остатки
        products = get_all_products()
        stocks_info = get_stocks_info()  # Нужно добавить эту функцию в magnit_api.py

        if not products:
            await update.message.reply_text("❌ Не удалось получить список товаров")
            return

        message = "📊 ТЕКУЩИЕ ОСТАТКИ:\n\n"

        sorted_products = sorted(
            products.items(),
            key=lambda x: x[1].get('seller_sku_id', 'N/A')
        )

        for i, (sku_id, product_info) in enumerate(sorted_products[:10], 1):
            seller_sku = product_info.get('seller_sku_id', 'N/A')
            title = product_info.get('title', 'N/A')
            stock_info = stocks_info.get(sku_id, {})
            stock = stock_info.get('stock', 0)
            reserved = stock_info.get('reserved', 0)

            message += f"{i}. {seller_sku} - {title}\n"
            message += f"   📦 Доступно: {stock} шт\n"
            message += f"   🔒 Зарезервировано: {reserved} шт\n\n"

        if len(sorted_products) > 10:
            message += f"... и еще {len(sorted_products) - 10} товаров"

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении остатков: {str(e)}")

async def sync_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Синхронизирует остатки"""
    await update.message.reply_text("🔄 Синхронизирую остатки...")

    success, message = sync_stocks_with_magnit()

    if success:
        await update.message.reply_text(f"✅ {message}")
    else:
        await update.message.reply_text(f"❌ {message}")


async def start_stock_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс редактирования остатка"""
    products = get_all_products()
    if not products:
        await update.message.reply_text("❌ Не удалось получить список товаров")
        return

    # Сохраняем продукты в контексте
    context.user_data['products'] = products
    context.user_data['state'] = 'waiting_stock_product'

    # Формируем список товаров
    message = "📦 Выберите товар для редактирования остатка:\n\n"

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


async def handle_stock_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор товара для редактирования остатка"""
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
            context.user_data['state'] = 'waiting_stock_value'

            await update.message.reply_text(
                f"✏️ Редактирование: {seller_sku}\n"
                f"📝 Название: {title}\n\n"
                f"Введите новый остаток:"
            )
        else:
            await update.message.reply_text("❌ Неверный номер товара")

    except ValueError:
        await update.message.reply_text("❌ Введите число")


async def handle_stock_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод нового значения остатка"""
    try:
        new_stock = int(update.message.text.strip())
        seller_sku = context.user_data.get('selected_product')
        title = context.user_data.get('selected_title')

        if new_stock < 0:
            await update.message.reply_text("❌ Остаток не может быть отрицательным")
            return

        await update.message.reply_text(f"🔄 Обновляю остаток {seller_sku}...")

        success, message = update_single_stock(seller_sku, new_stock)

        if success:
            await update.message.reply_text(f"✅ {message}")
        else:
            await update.message.reply_text(f"❌ {message}")

        # Сбрасываем состояние
        context.user_data.pop('state', None)
        context.user_data.pop('selected_product', None)
        context.user_data.pop('selected_title', None)
        context.user_data.pop('products', None)

        # Возвращаем в меню остатков
        await update.message.reply_text(
            "📊 Управление остатками\n\nВыберите действие:",
            reply_markup=get_stocks_keyboard()
        )

    except ValueError:
        await update.message.reply_text("❌ Введите число")