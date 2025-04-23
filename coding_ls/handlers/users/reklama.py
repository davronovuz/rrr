from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, bot, db
from data import config
import random


# Holatlar sinfi
class AdState(StatesGroup):
    waiting_for_ad = State()  # Reklama xabarini kutish
    confirm_ad = State()  # Reklamani tasdiqlash


# Admin tekshiruvi dekoratori
def admin_only(func):
    async def wrapper(message: types.Message, *args, **kwargs):
        # ADMINS ro‘yxati int sifatida ishlov beriladi
        try:
            admin_ids = [int(admin_id) for admin_id in config.ADMINS]
        except ValueError:
            await message.answer("❌ Config faylida admin ID’lar noto‘g‘ri kiritilgan!")
            return
        if message.from_user.id in admin_ids:
            await func(message, *args, **kwargs)
        else:
            await message.answer("❌ Bu buyruq faqat adminlar uchun!")

    return wrapper


# /reklom buyrug‘i: Reklama yuborish jarayonini boshlash
@dp.message_handler(commands="reklom", state="*")
@admin_only
async def start_ad_handler(message: types.Message, state: FSMContext, **kwargs):
    # Agar foydalanuvchi boshqa holatda bo‘lsa, holatni tozalash
    await state.finish()

    await message.answer(
        "📢 Reklama xabarini yuboring (matn, rasm, video, stiker va h.k.).\n"
        "Xabarni kiritganingizdan so‘ng tasdiqlashingiz mumkin.\n"
        "❗️ Eslatma: Juda uzun xabarlar foydalanuvchilarni bezovta qilishi mumkin!"
    )
    await state.set_state(AdState.waiting_for_ad)


# Har qanday xabar turi uchun reklama qabul qilish
@dp.message_handler(content_types=types.ContentType.ANY, state=AdState.waiting_for_ad)
@admin_only
async def receive_ad_handler(message: types.Message, state: FSMContext, **kwargs):
    # Xabarni saqlash
    await state.update_data(ad_message=message)

    # Tasdiqlash tugmalari
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_ad"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_ad")
        ]
    ])

    # Xabar turi haqida qisqacha ma'lumot
    ad_type = "noma'lum"
    if message.text:
        ad_type = f"matn ({len(message.text)} belgi)"
    elif message.photo:
        ad_type = "rasm"
    elif message.video:
        ad_type = "video"
    elif message.sticker:
        ad_type = "stiker"
    else:
        ad_type = "boshqa (masalan, hujjat yoki audio)"

    # Xabarni admin uchun ko‘rsatish
    if message.text:
        await message.answer(
            f"📝 Reklama turi: {ad_type}\n"
            f"Matn:\n{message.text}\n\nYuborishni tasdiqlaysizmi?",
            reply_markup=keyboard
        )
    elif message.photo:
        await message.answer_photo(
            message.photo[-1].file_id,
            caption=f"🖼️ Reklama turi: {ad_type}\n"
                    f"Tavsif: {message.caption or 'Yo‘q'}\n\n"
                    "Yuborishni tasdiqlaysizmi?",
            reply_markup=keyboard
        )
    elif message.video:
        await message.answer_video(
            message.video.file_id,
            caption=f"🎥 Reklama turi: {ad_type}\n"
                    f"Tavsif: {message.caption or 'Yo‘q'}\n\n"
                    "Yuborishni tasdiqlaysizmi?",
            reply_markup=keyboard
        )
    elif message.sticker:
        await message.answer_sticker(message.sticker.file_id)
        await message.answer(
            f"😄 Reklama turi: {ad_type}\n\nYuborishni tasdiqlaysizmi?",
            reply_markup=keyboard
        )
    else:
        await message.copy_to(chat_id=message.from_user.id)
        await message.answer(
            f"📎 Reklama turi: {ad_type}\n\nYuborishni tasdiqlaysizmi?",
            reply_markup=keyboard
        )

    await state.set_state(AdState.confirm_ad)


# Tasdiqlash yoki bekor qilish
@dp.callback_query_handler(state=AdState.confirm_ad)
@admin_only
async def process_ad_confirmation(callback: types.CallbackQuery, state: FSMContext, **kwargs):
    if callback.data == "cancel_ad":
        try:
            await callback.message.edit_text("❌ Reklama yuborish bekor qilindi.")
        except:
            # Agar xabar matnsiz bo‘lsa, yangi xabar yuboramiz
            await callback.message.delete()
            await callback.message.answer("❌ Reklama yuborish bekor qilindi.")
        await state.clear()
        return

    # Reklama xabarini olish
    data = await state.get_data()
    ad_message = data['ad_message']

    # Barcha foydalanuvchilarni olish
    users = await db.select_all_users()

    if not users:
        try:
            await callback.message.edit_text("😔 Hozirda foydalanuvchilar yo‘q. Reklama yuborilmadi.")
        except:
            await callback.message.delete()
            await callback.message.answer("😔 Hozirda foydalanuvchilar yo‘q. Reklama yuborilmadi.")
        await state.clear()
        return

    success_count = 0
    blocked_count = 0
    # Tasodifiy qiziqarli iboralar reklama xabariga qo‘shish uchun
    fun_phrases = [
        "🔥 Yangi imkoniyatlarni kashf eting!",
        "😎 Bu siz uchun maxsus taklif!",
        "🎉 Bugun yangi narsa sinab ko‘ring!"
    ]

    for user in users:
        try:
            # Xabarni foydalanuvchiga yuborish
            if ad_message.text:
                await bot.send_message(
                    user['telegram_id'],
                    f"{ad_message.text}\n\n{fun_phrases[random.randint(0, len(fun_phrases) - 1)]}"
                )
            elif ad_message.photo:
                await bot.send_photo(
                    user['telegram_id'],
                    ad_message.photo[-1].file_id,
                    caption=(ad_message.caption or "") + f"\n\n{fun_phrases[random.randint(0, len(fun_phrases) - 1)]}"
                )
            elif ad_message.video:
                await bot.send_video(
                    user['telegram_id'],
                    ad_message.video.file_id,
                    caption=(ad_message.caption or "") + f"\n\n{fun_phrases[random.randint(0, len(fun_phrases) - 1)]}"
                )
            elif ad_message.sticker:
                await bot.send_sticker(user['telegram_id'], ad_message.sticker.file_id)
                await bot.send_message(
                    user['telegram_id'],
                    fun_phrases[random.randint(0, len(fun_phrases) - 1)]
                )
            else:
                await ad_message.copy_to(chat_id=user['telegram_id'])
                await bot.send_message(
                    user['telegram_id'],
                    fun_phrases[random.randint(0, len(fun_phrases) - 1)]
                )
            success_count += 1
        except Exception:
            blocked_count += 1
            continue

    # Natijani ko‘rsatish
    result_message = (
        f"✅ Reklama {success_count} ta foydalanuvchiga muvaffaqiyatli yuborildi!\n"
        f"🚫 {blocked_count} ta foydalanuvchi botni bloklagan."
    )
    try:
        await callback.message.edit_text(result_message)
    except:
        # Agar xabar matnsiz bo‘lsa, avvalgi xabarni o‘chiramiz va yangi xabar yuboramiz
        await callback.message.delete()
        await callback.message.answer(result_message)

    await state.clear()