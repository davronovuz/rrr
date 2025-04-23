from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
import asyncpg

from data.config import ADMINS
from loader import dp,db,bot


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    telegram_id=message.from_user.id
    username=message.from_user.username
    full_name=message.from_user.full_name

    try:
        user=await db.add_user(full_name,username,telegram_id)

    except asyncpg.exceptions.UniqueViolationError:
        user=await db.select_user(telegram_id=telegram_id)

    await message.answer("Xush kelibsiz")


    #ADMINGA XABAR YUBORAMIZ
    count=await db.count_users()
    msg=f"{user[1]} bazaga qo'shildi \n"
    msg+=f"Bazada {count} ta foydalanuvchi bor"
    await bot.send_message(ADMINS[0],msg)



