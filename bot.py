import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Читаем конфигурацию из переменных окружения (удобно для Railway)
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Состояния для конечного автомата (FSM)
class TrackForm(StatesGroup):
  waiting_for_track = State()


# 1. Обработка команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
  greeting_text = (
      "Здравствуйте, вы можете порекомендовать трек для ТГК @airears\n"
      "Просто введите название трека и исполнителя и в скором времени ваш"
      " любимый трек будет в посте."
  )
  await message.answer(greeting_text)
  await state.set_state(TrackForm.waiting_for_track)


# 2. Получение трека, отправка админу и показ условий
@dp.message(TrackForm.waiting_for_track, F.text)
async def process_track(message: types.Message, state: FSMContext):
  track_info = message.text

  # Формируем юзернейм для отправки админу
  username = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else f"id{message.from_user.id} (без юзернейма)"
  )

  # Формируем сообщение для администратора в заданном формате
  admin_message = f"Трек - *{track_info}*\n\nОт: {username}"

  # Отправляем админу
  try:
    await bot.send_message(
        chat_id=ADMIN_ID, text=admin_message, parse_mode="Markdown"
    )
  except Exception as e:
    logging.error(f"Не удалось отправить сообщение админу: {e}")

  # Формируем текст с условиями и ссылку для пользователя
  agreement_text = (
      "Продолжив то-есть порекомендовав трек вы соглашаетесь на "
      '<a href="https://t.me/air_ears/2">условия использования</a>'
  )

  # Создаем инлайн-кнопки
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(text="Согласиться", callback_data="agree_terms"),
          InlineKeyboardButton(text="Отказаться", callback_data="decline_terms"),
      ]]
  )

  await message.answer(
      agreement_text, reply_markup=keyboard, parse_mode="HTML"
  )
  await state.clear()


# 3. Обработка нажатия кнопки "Согласиться"
@dp.callback_query(F.data == "agree_terms")
async def process_agree(callback: types.CallbackQuery):
  await callback.message.edit_text(
      "Спасибо! Ваш трек принят и скоро появится в канале @airears."
  )
  await callback.answer()


# 4. Обработка нажатия кнопки "Отказаться"
@dp.callback_query(F.data == "decline_terms")
async def process_decline(callback: types.CallbackQuery):
  await callback.message.edit_text(
      "Вы отказались от условий. Рекомендация трека отменена.\n"
      "Если захотите попробовать снова, просто отправьте /start."
  )
  await callback.answer()


# Запуск бота
async def main():
  logging.basicConfig(level=logging.INFO)
  print("Бот запущен...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
