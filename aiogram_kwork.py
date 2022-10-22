import asyncio
from kwork import Kwork
from config import TOKEN, ADMIN_ID
from aiogram import Bot, Dispatcher, executor, types

bot = Bot(token=TOKEN)
loop = asyncio.get_event_loop()
dp = Dispatcher(bot, loop=loop)
unread_names_ids = dict()

login_kwork = "Иди нахуй!"
passwork_kwork = "Иди нахуй!"


@dp.message_handler(commands=["start", "help"])
async def start(message: types.Message):
    if message.from_user.id == int(ADMIN_ID):
        await bot.send_message(message.from_user.id, "Команды: /help /check /authorization")
    else:
        await bot.send_message(message.from_user.id, "Команды: /help /check")


@dp.message_handler(commands=["check"])
async def check(message: types.Message):
    await bot.send_message(message.from_user.id, "Бот работает")


@dp.message_handler(commands=["authorization"])
async def authorization(message: types.Message):
    if message.from_user.id == int(ADMIN_ID):
        await bot.send_message(message.from_user.id, "Отправь логин и пароль через пробел")

        @dp.message_handler(content_types=["text"])
        async def input(message: types.Message):
            global login_kwork, passwork_kwork
            login_kwork, passwork_kwork = message.text.split(" ")
            await bot.send_message(message.from_user.id, "Отправлено")
    else:
        await bot.send_message(message.from_user.id, "Не, это не для тебя")


@dp.message_handler(commands=["answer"])
async def text(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    for user_name, user_id in unread_names_ids.items():
        markup.add(types.InlineKeyboardButton(user_name, callback_data=user_id))
    await bot.send_message(ADMIN_ID, "Выбери кому ответить", reply_markup=markup)


@dp.callback_query_handler(lambda user_id: user_id.data in unread_names_ids.values())
async def answer(message: types.Message):
    if message.from_user.id == int(ADMIN_ID):
        await bot.send_message(ADMIN_ID, "Напиши сообщение")

        @dp.message_handler(content_types=["text"])
        async def send_answer(answer: types.Message):
            try:
                api = Kwork(login=login_kwork, password=passwork_kwork, phone_last="7138")
                await api.send_message(user_id=int(message.data), text=answer.text)
                await api.close()
                await bot.send_message(ADMIN_ID, "Отправлено")
            except Exception as ex:
                await bot.send_message(ADMIN_ID, "Сообщение не отправлено")
                await bot.send_message(ADMIN_ID, f"{ex}")
                await api.close()
                return
            # Удаление непрочитанного
            for user_name, user_id in unread_names_ids.items():
                if int(message.data) == user_id:
                    del unread_names_ids[user_name]


async def get_unread_messages():
    while True:
        try:
            try:
                # api = Kwork(login=login_kwork, password=passwork_kwork)

                # Если "Необходимо ввести последние 4 цифры номера телефона."
                api = Kwork(login=login_kwork, password=passwork_kwork, phone_last="7138")
            except Exception as ex:
                await api.close()
                await bot.send_message(ADMIN_ID, f"{ex}")
                print(ex)
                continue
            # Получения всех диалогов на аккаунте
            all_dialogs = await api.get_all_dialogs()
            for line in all_dialogs:
                if line.unread_count > 0:
                    if line.user_id not in unread_names_ids.values():
                        unread_names_ids[line.username] = str(line.user_id)
                    await bot.send_message(ADMIN_ID,
                                           f"{line.username} ({line.unread_count}): {line.last_message}\nОтветить: /answer")
            await api.close()
        except Exception as ex:
            await bot.send_message(ADMIN_ID, f"{ex}")
        await asyncio.sleep(10)


if __name__ == '__main__':
    dp.loop.create_task(get_unread_messages())
    executor.start_polling(dp)
