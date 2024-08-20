#do stuff here

import aiosqlite
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F

logging.basicConfig(level=logging.INFO)

API_TOKEN = '5115173783:AAHRgcj341Bh0E9X4rKIqgGJ2a-lSb7cA10'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

DB_NAME = 'quiz_bot.db'

quiz_data = [
    {
        'question': 'Что такое Python?',
        'options': ['Язык программирования', 'Тип данных', 'Музыкальный инструмент', 'Змея на английском'],
        'correct_option': 0
    },
    {
        'question': 'Какой тип данных используется для хранения целых чисел?',
        'options': ['int', 'float', 'str', 'natural'],
        'correct_option': 0
    },
    {
        'question': 'Функция  int()',
        'options': ['не используется в данном языке программирования', 'преобразует строку из цифр в дробное число', 'преобразует строку из цифр в целое число'],
        'correct_option': 2
    },
    {
        'question': 'Как называется тип данных из неупорядоченных пар ключ-значение?',
        'options': ['set', 'dict', 'list', 'frozenset'],
        'correct_option': 1
    },
    {
        'question': 'Какое выражение верно для функций в Python?',
        'options': ['могут возвращать только одно значение', 'количество аргументов ограниченно', 'могут возвращать несколько значений', 'не возвращают ничего без return'],
        'correct_option': 2
    },
    {
        'question': 'В Python нет символьного типа данных',
        'options': ['True', 'False'],
        'correct_option': 0
    },
    {
        'question': 'Строки в Python могут быть модифицированы после создания',
        'options': ['True', 'False'],
        'correct_option': 1
    },
    {
        'question': 'Каким методом получится прочитать файл строка за строкой?',
        'options': ['read(1)', 'readlines(1)', 'readline()', 'line()'],
        'correct_option': 2
    },
    {
        'question': 'Какой метод выведет список файлов в папке?',
        'options': ['os.listfiles()', 'os.listdir()'],
        'correct_option': 1
    },
    {
        'question': 'Какой результат выведет код print(abs(-45.300))',
        'options': ['45.300', '-45.3', '-45.300', '45.3'],
        'correct_option': 3
    }
]

def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    builder.adjust(1)
    return builder.as_markup()

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
        
        
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await create_table()
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Готов начинать?", reply_markup=builder.as_markup(resize_keyboard=True))

async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)

async def new_quiz(message):
    user_id = message.from_user.id
    print(user_id)
    current_question_index = 0
    user_score = 0
    await initial_quiz_update(user_id, current_question_index, user_score)
    await get_question(message, user_id)

async def get_quiz_index(user_id):
     async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            results = await cursor.fetchone()

            if results is not None:
                return results[0]
            else:
                return 0
                        
async def get_user_score(user_id):
    print(f"Запрос оценки для пользователя {user_id}")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_score FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            results = await cursor.fetchone()

            if results is not None:
                logging.info(results[0])
                return results[0]
            else:
                return 0             

async def initial_quiz_update(user_id, index, score):
    logging.info(f'Начальная настройка БД:\nID: {user_id}\nQuestionID: {index}\nUserScore: {score}')
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, user_score) VALUES (?, ?, ?)', (user_id, index, score))
        await db.commit()


async def update_quiz_index(user_id, index, score):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, user_score) VALUES (?, ?, ?)', (user_id, index, score))
        await db.commit()

@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer(f"Начинаем квиз!")
    await new_quiz(message)


async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, user_score INTEGER)''')
        await db.commit()


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