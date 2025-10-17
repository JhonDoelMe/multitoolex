# bot_app/keyboard.py
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# ------------------------------------------------------------
# Основное меню (ReplyKeyboard)
# ------------------------------------------------------------
def main_menu() -> ReplyKeyboardMarkup:
    """
    Постоянная клавиатура (reply keyboard) под полем ввода.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎥 Скачати відео"),
                KeyboardButton(text="ℹ️ Інструкція"),
            ],
            [
                KeyboardButton(text="📜 Історія"),
                KeyboardButton(text="❌ Вийти"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Введіть посилання або виберіть дію…",
    )


# ------------------------------------------------------------
# Клавиатура «Назад»
# ------------------------------------------------------------
def back_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="↩️ Назад")]],
        resize_keyboard=True,
    )


# ------------------------------------------------------------
# Inline-клавиатуры (контекстные)
# ------------------------------------------------------------
def confirm_download(token: str) -> InlineKeyboardMarkup:
    """
    ВАЖНО: В callback_data нельзя класть длинные строки (лимит Telegram ~64 байта).
    Поэтому сюда передаём короткий токен (например, 'abc123'), а сам URL
    храним во временном кеше в handlers.py.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"download:{token}"),
                InlineKeyboardButton(text="❌ Відмінити", callback_data="cancel"),
            ]
        ]
    )


def download_finished(file_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📂 Відкрити файл", callback_data=f"open:{file_id}"),
                InlineKeyboardButton(text="↩️ Меню", callback_data="back_to_menu"),
            ]
        ]
    )
