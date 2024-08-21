import aiosqlite
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
from quiz_data import quiz_data
from async_quiz_functions import *

logging.basicConfig(level=logging.INFO)

API_TOKEN = '5115173783:AAHRgcj341Bh0E9X4rKIqgGJ2a-lSb7cA10'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

DB_NAME = 'quiz_bot.db'

#Колбэки квиза
@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index = await get_quiz_index(callback.from_user.id)
    current_answer = quiz_data[current_question_index]['options'][quiz_data[current_question_index]['correct_option']]
    await callback.message.answer(f"[ {current_answer} ]\nВерно!")
    current_question_index += 1
    current_score = await get_user_score(callback.from_user.id)
    current_score += 1

    await update_quiz_index(callback.from_user.id, current_question_index, current_score)

    new_score = await get_user_score(callback.from_user.id)
    await callback.message.answer(f'Текущий результат: {new_score}')

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Квиз завершен!")
        await callback.message.answer(f'Итоговый результат: {new_score} / {len(quiz_data)}')


@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']

    await callback.message.answer(f"Неверно. Ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    current_question_index += 1
    current_score = await get_user_score(callback.from_user.id)
    await update_quiz_index(callback.from_user.id, current_question_index, current_score)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Квиз завершен!")
        
#Хендлеры команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await create_table()
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Готов начинать?", reply_markup=builder.as_markup(resize_keyboard=True))


@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer(f"Начинаем квиз!")
    await new_quiz(message)

@dp.message(F.text=="Стоп")
@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('DROP TABLE quiz_state'):
            await message.answer("Бот остановлен")

async def main():
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())