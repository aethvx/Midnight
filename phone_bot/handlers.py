from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from phone_bot.config import Config
from phone_bot.database import Database, REGULAR, REPLACEMENT
from phone_bot.keyboards import admin_keyboard


class AddPhones(StatesGroup):
    waiting_for_numbers = State()


def build_router(config: Config, database: Database) -> Router:
    router = Router()

    def is_admin(user_id: int | None) -> bool:
        return user_id is not None and user_id in config.admin_ids

    @router.message(CommandStart(), F.chat.type == "private")
    async def start(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id if message.from_user else None):
            return
        await state.clear()
        await message.answer(
            "Управление очередями номеров:", reply_markup=admin_keyboard()
        )

    @router.message(Command("cancel"), F.chat.type == "private")
    async def cancel_command(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id if message.from_user else None):
            return
        await state.clear()
        await message.answer("Добавление отменено.", reply_markup=admin_keyboard())

    @router.callback_query(F.data == "cancel")
    async def cancel_button(callback: CallbackQuery, state: FSMContext) -> None:
        if not is_admin(callback.from_user.id):
            await callback.answer()
            return
        await state.clear()
        await callback.answer("Отменено")
        if callback.message:
            await callback.message.answer(
                "Управление очередями:", reply_markup=admin_keyboard()
            )

    @router.callback_query(F.data.startswith("add:"))
    async def choose_queue(callback: CallbackQuery, state: FSMContext) -> None:
        if not is_admin(callback.from_user.id):
            await callback.answer()
            return
        queue_type = callback.data.split(":", 1)[1]
        if queue_type not in {REGULAR, REPLACEMENT}:
            await callback.answer("Неизвестная очередь", show_alert=True)
            return
        await state.set_state(AddPhones.waiting_for_numbers)
        await state.update_data(queue_type=queue_type)
        queue_name = (
            "обычную очередь" if queue_type == REGULAR else "очередь на перестановку"
        )
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                f"Отправь номера в {queue_name}: по одному номеру на строке.\n"
                "Для отмены нажми кнопку или отправь /cancel.",
                reply_markup=admin_keyboard(),
            )

    @router.message(AddPhones.waiting_for_numbers, F.chat.type == "private")
    async def receive_numbers(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id if message.from_user else None):
            return
        if not message.text:
            await message.answer("Нужен текст: по одному номеру на строке.")
            return

        data = await state.get_data()
        result = await database.add_phones(
            message.text.splitlines(), data["queue_type"]
        )
        await state.clear()
        parts = [f"Добавлено: {result.added}."]
        if result.duplicates:
            parts.append(f"Уже были в очереди: {result.duplicates}.")
        if result.invalid:
            shown = ", ".join(result.invalid[:5])
            suffix = "…" if len(result.invalid) > 5 else ""
            parts.append(f"Не распознаны: {shown}{suffix}.")
        await message.answer(" ".join(parts), reply_markup=admin_keyboard())

    @router.callback_query(F.data == "stats")
    async def show_stats(callback: CallbackQuery) -> None:
        if not is_admin(callback.from_user.id):
            await callback.answer()
            return
        counts = await database.counts()
        issued = await database.total_issued()
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                f"Обычные: {counts[REGULAR]}\n"
                f"На перестановку: {counts[REPLACEMENT]}\n"
                f"Всего выдано: {issued}",
                reply_markup=admin_keyboard(),
            )

    @router.callback_query(F.data == "preview")
    async def show_preview(callback: CallbackQuery) -> None:
        if not is_admin(callback.from_user.id):
            await callback.answer()
            return
        regular = await database.queue_preview(REGULAR)
        replacement = await database.queue_preview(REPLACEMENT)

        def format_queue(title: str, phones: list[str]) -> str:
            body = "\n".join(phones) if phones else "— пусто —"
            return f"{title}:\n{body}"

        await callback.answer()
        if callback.message:
            await callback.message.answer(
                f"{format_queue('Обычные (первые 20)', regular)}\n\n"
                f"{format_queue('На перестановку (первые 20)', replacement)}",
                reply_markup=admin_keyboard(),
            )

    @router.message(F.text)
    async def issue_phone(message: Message, bot: Bot) -> None:
        if message.text.strip().casefold() != "вотс":
            return
        if message.chat.id != config.group_id:
            return
        if message.message_thread_id != config.topic_id:
            return
        if message.from_user is None or message.from_user.id != config.requester_id:
            return

        issued = await database.issue_next(
            requester_id=message.from_user.id,
            chat_id=message.chat.id,
            topic_id=message.message_thread_id,
        )
        text = issued.phone if issued else "Номеров нет"
        await bot.send_message(
            chat_id=message.chat.id,
            message_thread_id=message.message_thread_id,
            text=text,
        )

    return router
