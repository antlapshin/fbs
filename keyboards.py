from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    """Основная клавиатура"""
    keyboard = [
        [KeyboardButton("📦 Новые заказы"), KeyboardButton("🔄 Синхронизация")],
        [KeyboardButton("📊 Остатки"), KeyboardButton("💰 Цены")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_sync_keyboard():
    """Клавиатура для синхронизации"""
    keyboard = [
        [KeyboardButton("🔄 Синхронизировать остатки"), KeyboardButton("💰 Синхронизировать цены")],
        [KeyboardButton("🔄 Синхронизировать всё"), KeyboardButton("📦 Ручное управление остатками")],
        [KeyboardButton("💰 Ручное управление ценами"), KeyboardButton("⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_stocks_keyboard():
    """Клавиатура для управления остатками"""
    keyboard = [
        [KeyboardButton("📊 Текущие остатки"), KeyboardButton("🔄 Синхронизировать остатки")],
        [KeyboardButton("✏️ Изменить остаток"), KeyboardButton("⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_prices_keyboard():
    """Клавиатура для управления ценами"""
    keyboard = [
        [KeyboardButton("💰 Текущие цены"), KeyboardButton("🔄 Синхронизировать цены")],
        [KeyboardButton("✏️ Изменить цену"), KeyboardButton("⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """Клавиатура с кнопкой Назад"""
    keyboard = [[KeyboardButton("⬅️ Назад")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)