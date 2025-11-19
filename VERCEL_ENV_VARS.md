# Переменные окружения для Vercel

Добавьте эти переменные в Vercel Dashboard → Settings → Environment Variables:

## Обязательные переменные:

1. **TELEGRAM_BOT_TOKEN** - токен вашего Telegram бота (получить у @BotFather)
2. **ADMIN_IDS** - ID администраторов через запятую (например: `123456789,987654321`)
3. **MAGNIT_API_KEY** - API ключ Magnit
4. **OZON_API_KEY** - API ключ Ozon
5. **OZON_CLIENT_ID** - Client ID Ozon
6. **WAREHOUSE_ID** - ID склада

## Как получить TELEGRAM_BOT_TOKEN:
1. Напишите @BotFather в Telegram
2. Отправьте `/mybots`
3. Выберите вашего бота
4. Выберите "API Token"

## Как получить ADMIN_IDS:
1. Напишите боту `/myid` (если он уже работает локально)
2. Или используйте @userinfobot в Telegram

## После добавления переменных:
1. Перезапустите деплой (Redeploy) или сделайте новый коммит
2. Проверьте логи в Vercel Dashboard → Logs

