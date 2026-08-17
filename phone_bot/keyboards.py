from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Обычные", callback_data="add:regular"),
                InlineKeyboardButton(
                    text="🔄 На перестановку", callback_data="add:replacement"
                ),
            ],
            [
                InlineKeyboardButton(text="📊 Остаток", callback_data="stats"),
                InlineKeyboardButton(
                    text="📋 Показать очереди", callback_data="preview"
                ),
            ],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ]
    )
