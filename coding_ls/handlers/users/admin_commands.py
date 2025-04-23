import random

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from loader import dp,bot,db



@dp.message_handler(commands="profile")
async def profile_handler(message: types.Message):
    user_id = message.from_user.id
    user = await db.select_user(telegram_id=user_id)

    if user:
        profile_text = (
            "👤 Sizning profilingiz:\n\n"
            f"🆔 ID: {user['id']}\n"
            f"📛 Ism: {user['full_name']}\n"
            f"👾 Username: {user['username'] or 'Yo‘q'}\n"
            f"📲 Telegram ID: {user['telegram_id']}"
        )
    else:
        profile_text = "❌ Siz hali ro‘yxatdan o‘tmagansiz. /start buyrug‘ini ishlatib ko‘ring!"

    await message.answer(profile_text)


@dp.message_handler(commands="stats")
async def stats_handler(message: types.Message):
    total_users = await db.count_users()
    # Eng oxirgi qo‘shilgan foydalanuvchi
    last_user = await db.execute("SELECT full_name FROM Users ORDER BY id DESC LIMIT 1", fetchval=True)

    stats_text = (
        "📊 Bot statistikasi:\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"🆕 Eng oxirgi foydalanuvchi: {last_user or 'Hali yo‘q'}\n"
    )
    await message.answer(stats_text)





class GuessNumberState(StatesGroup):
    playing = State()



@dp.message_handler(commands="guess")
async def guess_number_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await db.select_user(telegram_id=user_id)

    if not user:
        await message.answer("❌ Avval /start buyrug‘ini ishlatib ro‘yxatdan o‘ting!")
        return

    # Tasodifiy raqam tanlash
    secret_number = random.randint(1, 100)
    await state.update_data(secret_number=secret_number, attempts=0)

    await message.answer(
        "🎲 Men 1 dan 100 gacha raqam o‘yladim. Uni taxmin qilib ko‘ring!\n"
        "Raqam kiriting:"
    )
    await state.set_state(GuessNumberState.playing)


@dp.message_handler(state=GuessNumberState.playing)
async def process_guess(message: types.Message, state: FSMContext):
    try:
        guess = int(message.text)
        data = await state.get_data()
        secret_number = data['secret_number']
        attempts = data['attempts'] + 1

        if guess == secret_number:
            points = max(10 - attempts, 1)  # Kamroq urinish = ko‘proq ball
            await message.answer(
                f"🎉 Tabriklaymiz! Siz {attempts} urinishda to‘g‘ri topdingiz! +{points} ball!"
            )
            await state.clear()
        elif guess < secret_number:
            await state.update_data(attempts=attempts)
            await message.answer("⬆️ Kattaroq raqam kiriting!")
        else:
            await state.update_data(attempts=attempts)
            await message.answer("⬇️ Kichikroq raqam kiriting!")
    except ValueError:
        await message.answer("❌ Iltimos, faqat raqam kiriting!")