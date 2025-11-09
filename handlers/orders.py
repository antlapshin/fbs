from telegram import Update
from telegram.ext import CallbackContext
from magnit_api import get_unprocessed_orders, get_all_products


async def show_orders(update: Update, context: CallbackContext):
    """Показывает новые заказы"""
    await update.message.reply_text("📦 Получаю информацию о заказах...")

    try:
        orders = get_unprocessed_orders()
        products = get_all_products()

        if not orders:
            await update.message.reply_text("✅ Нет необработанных заказов")
            return

        message = f"📦 НЕОБРАБОТАННЫЕ ЗАКАЗЫ ({len(orders)}):\n\n"

        for i, order in enumerate(orders, 1):
            order_id = order.get('order_id', 'N/A')
            status = order.get('status', 'N/A')
            items = order.get('items', [])

            message += f"🆔 Заказ: {order_id}\n"
            message += f"📊 Статус: {status}\n"
            message += f"📦 Товаров: {len(items)}\n"

            for j, item in enumerate(items, 1):
                sku_id = str(item.get('sku_id', 'N/A'))
                quantity = item.get('quantity', 0)
                product_info = products.get(sku_id, {})
                seller_sku_id = product_info.get('seller_sku_id', 'N/A')
                title = product_info.get('title', f'Товар {sku_id}')

                connector = "└─" if j == len(items) else "├─"
                message += f"  {connector} {seller_sku_id}: {title} - {quantity} шт\n"

            message += "\n" + "─" * 40 + "\n\n"

        # Разбиваем сообщение если оно слишком длинное
        if len(message) > 4096:
            parts = [message[i:i + 4096] for i in range(0, len(message), 4096)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении заказов: {str(e)}")