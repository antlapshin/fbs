import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, ADMIN_IDS

from handlers.orders import show_orders
from handlers.stocks import (
    show_stocks_menu, sync_stocks, start_stock_edit,
    handle_stock_product_selection, handle_stock_value_input, show_current_stocks
)
from handlers.prices import (
    show_prices_menu, sync_prices, start_price_edit,
    handle_price_product_selection, handle_price_value_input, show_current_prices
)

from keyboards import get_main_keyboard, get_sync_keyboard
from magnit_api import sync_stocks_with_magnit, sync_prices_with_magnit

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    logger.info(f"🔍 User {user_id} ({update.effective_user.username or 'no username'}) tried /start")
    logger.info(f"🔑 ADMIN_IDS: {ADMIN_IDS}")
    
    if not is_admin(user_id):
        logger.warning(f"❌ Access denied for user {user_id}")
        await update.message.reply_text("❌ У вас нет доступа к этому боту")
        return

    welcome_text = (
        "🤖 Бот управления Magnit Marketplace\n\n"
        "Доступные функции:\n"
        "📦 - Просмотр новых заказов\n"
        "📊 - Управление остатками\n"
        "💰 - Управление ценами\n"
        "🔄 - Синхронизация данных\n\n"
        "Выберите действие:"
    )

    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту")
        return

    text = update.message.text
    user_state = context.user_data.get('state')

    # Проверяем состояния пользователя из context.user_data
    if user_state == 'waiting_stock_product':
        await handle_stock_product_selection(update, context)
        return
    elif user_state == 'waiting_stock_value':
        await handle_stock_value_input(update, context)
        return
    elif user_state == 'waiting_price_product':
        await handle_price_product_selection(update, context)
        return
    elif user_state == 'waiting_price_value':
        await handle_price_value_input(update, context)
        return

    # Обработка основных команд
    if text == "📦 Новые заказы":
        await show_orders(update, context)

    elif text == "🔄 Синхронизация":
        await update.message.reply_text(
            "🔄 Синхронизация данных\n\nВыберите действие:",
            reply_markup=get_sync_keyboard()
        )

    elif text == "📊 Остатки":
        await show_stocks_menu(update, context)

    elif text == "💰 Цены":
        await show_prices_menu(update, context)

    elif text == "ℹ️ Помощь":
        await show_help(update, context)

    # Обработка команд синхронизации
    elif text == "🔄 Синхронизировать остатки":
        await sync_stocks(update, context)

    elif text == "💰 Синхронизировать цены":
        await sync_prices(update, context)

    elif text == "🔄 Синхронизировать всё":
        await sync_all(update, context)

    elif text == "📦 Ручное управление остатками":
        await start_stock_edit(update, context)

    elif text == "💰 Ручное управление ценами":
        await start_price_edit(update, context)

    # Обработка команд из меню остатков
    elif text == "📊 Текущие остатки":
        await show_current_stocks(update, context)

    elif text == "✏️ Изменить остаток":
        await start_stock_edit(update, context)

    # Обработка команд из меню цен
    elif text == "💰 Текущие цены":
        await show_current_prices(update, context)

    elif text == "✏️ Изменить цену":
        await start_price_edit(update, context)

    elif text == "⬅️ Назад":
        # Сбрасываем состояние при возврате в главное меню
        context.user_data.pop('state', None)
        context.user_data.pop('products', None)
        context.user_data.pop('selected_product', None)
        context.user_data.pop('selected_title', None)

        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_keyboard()
        )

    else:
        await update.message.reply_text(
            "Не понимаю команду. Используйте кнопки меню.",
            reply_markup=get_main_keyboard()
        )


async def sync_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Синхронизирует всё"""
    await update.message.reply_text("🔄 Начинаю полную синхронизацию...")

    # Синхронизация остатков
    success_stocks, message_stocks = sync_stocks_with_magnit()
    stocks_msg = f"📊 Остатки: {'✅' if success_stocks else '❌'} {message_stocks}\n"
    await update.message.reply_text(stocks_msg)

    # Синхронизация цен
    success_prices, message_prices = sync_prices_with_magnit()
    prices_msg = f"💰 Цены: {'✅' if success_prices else '❌'} {message_prices}\n"
    await update.message.reply_text(prices_msg)

    if success_stocks and success_prices:
        await update.message.reply_text("🎉 Полная синхронизация завершена успешно!")
    else:
        await update.message.reply_text("⚠️ Синхронизация завершена с ошибками")


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает справку"""
    help_text = (
        "🤖 Помощь по боту управления Magnit Marketplace\n\n"
        "📦 <b>Новые заказы</b> - просмотр необработанных заказов\n"
        "📊 <b>Остатки</b> - управление остатками товаров\n"
        "💰 <b>Цены</b> - управление ценами товаров\n"
        "🔄 <b>Синхронизация</b> - синхронизация данных с Ozon\n\n"
        "<i>Для работы бота требуется доступ к API Magnit и Ozon</i>"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')


async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения своего ID"""
    user_id = update.effective_user.id
    await update.message.reply_text(f"🆔 Ваш ID: {user_id}\n\nДобавьте его в ADMIN_IDS в файле .env")


def register_handlers(application: Application) -> None:
    """Добавляет все обработчики в экземпляр Application."""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", get_my_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


def create_application() -> Application:
    """Создает и возвращает Telegram Application с зарегистрированными обработчиками."""
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    register_handlers(application)
    return application


async def initialize_application() -> Application:
    """Создает приложение и выполняет инициализацию без запуска polling."""
    application = create_application()
    await application.initialize()
    await application.start()
    return application


async def process_update_with_application(update_data: dict, application: Application) -> None:
    """Обрабатывает обновление Telegram, используя готовое приложение."""
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)


async def main_async():
    """Основная асинхронная функция бота (режим polling)."""
    print("🚀 Starting Magnit Bot...")

    try:
        application = create_application()
    except RuntimeError as error:
        print(f"❌ ERROR: {error}")
        return

    print("✅ Бот инициализирован! Запускаем polling...")

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    print("🎉 Бот запущен и работает!")

    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("🛑 Остановка бота...")
    except Exception as e:
        print(f"❌ Ошибка в основном цикле: {e}")
    finally:
        print("⏹️ Завершаем работу бота...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        print("👋 Бот остановлен")


async def simple_main():
    """Упрощенная версия запуска (polling) для локальной отладки."""
    print("🚀 Starting Magnit Bot (simple mode)...")

    try:
        application = create_application()
    except RuntimeError as error:
        print(f"❌ ERROR: {error}")
        return

    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        print("🎉 Бот запущен и работает!")

        while True:
            await asyncio.sleep(10)
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        raise
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


def main():
    """Синхронная обертка для обратной совместимости."""
    asyncio.run(simple_main())


if __name__ == "__main__":
    main()