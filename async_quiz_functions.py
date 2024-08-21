from main import aiosqlite, DB_NAME, logging
from quiz_data import quiz_data
from bot_keyboard import generate_options_keyboard

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

async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, user_score INTEGER)''')
        await db.commit()