from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database
import aiosqlite
from config import ADMINS, MOVIE_CHANNEL, TELEGRAM_CHANNELS
from keyboards.reply import admin_reply_keyboard
from keyboards.inline import (
    admin_approval_keyboard,
    admin_customers_menu,
    admin_user_list_keyboard,
    admin_user_manage_keyboard,
    admin_limit_give_keyboard,
    admin_balance_manage_menu,
    admin_back_button,
    admin_keyboard
)
from keyboards.reply import admin_reply_keyboard, back_reply_keyboard

admin_router = Router()

class MovieState(StatesGroup):
    waiting_for_title = State()
    waiting_for_code = State()
    waiting_for_duration = State()
    waiting_for_coin = State()
    waiting_for_video = State()
    waiting_for_del_code = State()

class ChannelState(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_url = State()
    waiting_for_ext_link = State()
    waiting_for_ext_name = State()
    waiting_for_channel_reward = State()
    waiting_for_del_id = State()

class AdminState(StatesGroup):
    viewing_applications = State()
    waiting_for_balance_amount = State()
    waiting_for_search_id = State()

def cancel_keyboard(text="⬅️ Orqaga qaytish", callback="cancel_admin_action"):
    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data=callback)
    return builder.as_markup()

def channel_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Telegram kanal", callback_data="add_chan_telegram")
    builder.button(text="▶️ YouTube kanal", callback_data="add_chan_youtube")
    builder.button(text="📸 Instagram sahifa", callback_data="add_chan_instagram")
    builder.adjust(1)
    return builder.as_markup()

def _channel_type_icon(ch):
    url = ch[2] or ""
    if ch[1] < 0:
        return "📱"
    elif "youtube.com" in url or "youtu.be" in url:
        return "▶️"
    elif "instagram.com" in url:
        return "📸"
    return "🔗"

_ADMINS_SET = set(ADMINS)

@admin_router.callback_query(F.data == "cancel_admin_action", F.from_user.id.in_(_ADMINS_SET))
@admin_router.message(F.text == "⬅️ Orqaga qaytish", F.from_user.id.in_(_ADMINS_SET))
async def cancel_admin_action(event: Message | CallbackQuery, state: FSMContext):
    # Faqat adminlar uchun. Oddiy foydalanuvchilar uchun filter False qaytaradi
    # va xabar avtomatik tarzda keyingi (user_router) ga o'tkaziladi.
    await state.clear()
    msg = "🏠 Admin paneliga qaytdingiz."
    if isinstance(event, CallbackQuery):
        await event.message.answer(msg, reply_markup=admin_reply_keyboard())
        await event.answer()
    else:
        await event.answer(msg, reply_markup=admin_reply_keyboard())

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id in ADMINS:
        return await message.answer(
            "💎 <b>Admin boshqaruv paneli</b>\n\nKerakli bo'limni tanlang:", 
            parse_mode="HTML",
            reply_markup=admin_keyboard()
        )

# StateFilter(None) — bu handlerlar faqat state bo'lmaganda ishlaydi
# Shunda kino qo'shish/o'chirish jarayonida boshqa bo'limga o'tib ketmaydi

@admin_router.message(StateFilter(None), F.text == "📊 Statistika")
@admin_router.callback_query(F.data == "admin_stats")
async def process_admin_stats(event: Message | CallbackQuery, state: FSMContext):
    user_id = event.from_user.id
    if user_id in ADMINS:
        try:
            total_users, active_today, total_requests = await database.get_statistics()
            text = (
                f"📊 <b>Umumiy statistika</b>\n\n"
                f"👥 Barcha foydalanuvchilar: <b>{total_users}</b> ta\n"
                f"🟢 Oxirgi 24 soatda faol: <b>{active_today}</b> ta\n"
                f"🎬 Jami ko'rilgan kinolar: <b>{total_requests}</b> marta\n"
            )
            if isinstance(event, Message):
                await event.answer(text, parse_mode="HTML", reply_markup=admin_back_button())
            else:
                await event.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back_button())
                await event.answer()
        except Exception as e:
            msg = f"Xatolik: {e}"
            if isinstance(event, Message): await event.answer(msg)
            else: await event.message.answer(msg)

@admin_router.message(StateFilter(None), F.text == "💰 Balans boshqaruvi")
async def process_admin_balance_menu(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        text = (
            "💰 <b>Balans va Statistika boshqaruvi</b>\n\n"
            "Pastdagi tugmalar orqali kerakli ma'lumotlarni ko'rishingiz mumkin."
        )
        await message.answer(text, parse_mode="HTML", reply_markup=admin_balance_manage_menu())

@admin_router.callback_query(F.data == "admin_total_income")
async def process_admin_total_income(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        from config import ADMIN_CARD, ADMIN_CARD_NAME
        _, _, total_income = await database.get_extended_statistics()
        text = (
            "💰 <b>Umumiy tushum ma'lumotlari</b>\n\n"
            f"📊 Jami tushgan mablag': <b>{total_income:,}</b> so'm\n\n"
            f"💳 Karta: <code>{ADMIN_CARD}</code>\n"
            f"👤 Egasi: <b>{ADMIN_CARD_NAME}</b>\n\n"
            "<i>Ushbu summa tasdiqlangan barcha to'lovlar yig'indisidir.</i>"
        )
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_balance_manage_menu())
        await call.answer()

@admin_router.callback_query(F.data == "admin_daily_income")
async def process_admin_daily_income(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        from config import ADMIN_CARD, ADMIN_CARD_NAME
        _, daily_income, _ = await database.get_extended_statistics()
        text = (
            "📅 <b>Bugungi tushum ma'lumotlari</b>\n\n"
            f"📊 Bugungi tushgan mablag': <b>{daily_income:,}</b> so'm\n\n"
            f"💳 Karta: <code>{ADMIN_CARD}</code>\n"
            f"👤 Egasi: <b>{ADMIN_CARD_NAME}</b>\n\n"
            "<i>Ushbu summa bugun tasdiqlangan to'lovlar yig'indisidir.</i>"
        )
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_balance_manage_menu())
        await call.answer()

@admin_router.callback_query(F.data == "admin_purchased_list")
async def process_admin_purchased_list(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        apps = await database.get_approved_applications()
        if not apps:
            return await call.answer("Hozircha sotib olganlar yo'q!", show_alert=True)
        text = "📜 <b>Sotib olganlar ro'yxati (Oxirgi 30 tasi):</b>\n\n"
        for i, app in enumerate(apps[:30], 1):
            if app[5] == 'PREMIUM':
                type_text = "💎 Prem"
                amount_text = f"{app[4]} oy"
            elif app[5] == 'LIMIT':
                type_text = "🎫 Limit"
                amount_text = f"{app[6]:,} so'm"
            else:
                type_text = "💰 Balans"
                amount_text = f"{app[6]:,} so'm"
            text += f"{i}. {app[2]} (<code>{app[1]}</code>) - <b>{amount_text}</b> ({type_text})\n"
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_balance_manage_menu())
        await call.answer()

@admin_router.message(StateFilter(None), F.text == "👥 Mijozlar")
async def admin_customers_start(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer(
            "👥 <b>Mijozlar boshqaruvi bo'limi</b>\n\nPastdagi menyu orqali kerakli bo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=admin_customers_menu()
        )

@admin_router.message(StateFilter(None), F.text == "📩 Murojaatlar")
async def view_applications_handler(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        apps = await database.get_pending_applications()
        if not apps:
            return await message.answer("📩 Hozircha yangi murojaatlar (to'lov cheklari) yo'q.", reply_markup=admin_back_button())
        await message.answer(f"📩 Jami {len(apps)} ta kutilayotgan murojaat bor. Birinchisini ko'rsataman:", reply_markup=admin_back_button())
        app = apps[0]
        if app[5] == 'PREMIUM':
            type_text = "💎 PREMIUM"
            amount_text = f"{app[4]} oylik"
        elif app[5] == 'LIMIT':
            type_text = "🎫 LIMIT (5 ta kino)"
            amount_text = f"{app[6]:,} so'm"
        else:
            type_text = "💰 BALANS"
            amount_text = f"{app[6]:,} so'm"
        await message.answer_photo(
            app[3],
            caption=(
                f"📩 <b>Yangi murojaat!</b>\n\n"
                f"👤 Foydalanuvchi: {app[2]}\n"
                f"🆔 ID: <code>{app[1]}</code>\n"
                f"📂 Turi: <b>{type_text}</b>\n"
                f"💵 Miqdori: <b>{amount_text}</b>\n"
                f"📅 Sana: {app[8]}\n\n"
                f"Tasdiqlaysizmi?"
            ),
            parse_mode="HTML",
            reply_markup=admin_approval_keyboard(app[0])
        )

# ─── Kino qo'shish ────────────────────────────────────────────────────────────

@admin_router.message(StateFilter(None), F.text == "➕ Kino/Multfilm qo'shish")
@admin_router.callback_query(F.data == "admin_add_movie")
async def add_movie_start(event: Message | CallbackQuery, state: FSMContext):
    if event.from_user.id in ADMINS:
        text = (
            "🎬 <b>Kino/Multfilm qo'shish</b>\n\n"
            "1-qadam: Kino/Multfilm <b>nomini</b> yozing:"
        )
        if isinstance(event, Message):
            await event.answer(text, parse_mode="HTML", reply_markup=back_reply_keyboard())
        else:
            await event.message.answer(text, parse_mode="HTML", reply_markup=back_reply_keyboard())
            await event.answer()
        await state.set_state(MovieState.waiting_for_title)

@admin_router.message(MovieState.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        if not message.text:
            return await message.answer(
                "⚠️ Iltimos, nom yozing.",
                reply_markup=cancel_keyboard()
            )
        title = message.text.strip()
        if not title:
            return await message.answer("⚠️ Nomi bo'sh bo'lmasin.", reply_markup=cancel_keyboard())
        await state.update_data(title=title)
        await message.answer(
            f"✅ Nomi qabul qilindi: <b>{title}</b>\n\n"
            "2-qadam: Kino uchun <b>kod</b> yozing (raqam yoki harf):\n"
            "Misol: <code>115</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(MovieState.waiting_for_code)

@admin_router.message(MovieState.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        if not message.text:
            return await message.answer("⚠️ Iltimos, matn ko'rinishida kod yozing.", reply_markup=cancel_keyboard())
        code = message.text.strip()
        if not code:
            return await message.answer("⚠️ Kod bo'sh bo'lmasin.", reply_markup=cancel_keyboard())
        await state.update_data(code=code)
        await message.answer(
            f"✅ Kod qabul qilindi: <code>{code}</code>\n\n"
            "3-qadam: Kino <b>vaqtini</b> kiriting:\n"
            "Misol: <code>1:45:00</code> yoki <code>105 daqiqa</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(MovieState.waiting_for_duration)

@admin_router.message(MovieState.waiting_for_duration)
async def process_duration(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        if not message.text:
            return await message.answer("⚠️ Iltimos, vaqt kiriting.", reply_markup=cancel_keyboard())
        duration = message.text.strip()
        if not duration:
            return await message.answer("⚠️ Vaqt bo'sh bo'lmasin.", reply_markup=cancel_keyboard())
        await state.update_data(duration=duration)
        await message.answer(
            "4-qadam: Kino uchun <b>coin</b> narxini kiriting (faqat son):\n"
            "Misol: <code>1</code> yoki <code>2</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(MovieState.waiting_for_coin)

@admin_router.message(MovieState.waiting_for_coin)
async def process_coin(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        if not message.text or not message.text.strip().isdigit():
            return await message.answer("⚠️ Coin faqat musbat butun son bo'lishi kerak.", reply_markup=cancel_keyboard())
        coin_cost = int(message.text.strip())
        if coin_cost <= 0:
            return await message.answer("⚠️ Coin 0 dan katta bo'lishi kerak.", reply_markup=cancel_keyboard())
        await state.update_data(coin_cost=coin_cost)
        await message.answer(
            "5-qadam: Endi kino faylini yuboring (video yoki document):",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(MovieState.waiting_for_video)

@admin_router.message(MovieState.waiting_for_video)
async def process_video(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        file_id = None
        if message.video:
            file_id = message.video.file_id
        elif message.document:
            file_id = message.document.file_id

        if not file_id:
            return await message.answer(
                "⚠️ Iltimos, video yoki document fayl yuboring.",
                reply_markup=cancel_keyboard()
            )

        data = await state.get_data()
        success = await database.add_movie(
            data['code'],
            data['title'],
            "kino",
            file_id,
            data.get('duration', ''),
            data.get('coin_cost', 1)
        )
        await state.clear()
        if success:
            await message.answer(
                f"✅ <b>Saqlandi!</b>\n\n"
                f"🎬 Nomi: {data['title']}\n"
                f"🔢 Kino kodi: <code>{data['code']}</code>\n"
                f"⏱️ Vaqti: {data.get('duration', '-')}\n"
                f"💰 Coin: {data.get('coin_cost', 1)}",
                parse_mode="HTML",
                reply_markup=admin_reply_keyboard()
            )
        else:
            await message.answer(
                f"⚠️ <b>{data['code']}</b> kodi allaqachon mavjud. Boshqa kod bilan qayta urinib ko'ring.",
                parse_mode="HTML",
                reply_markup=admin_reply_keyboard()
            )

# ─── Kino o'chirish ───────────────────────────────────────────────────────────

@admin_router.message(StateFilter(None), F.text == "🗑 Kino/Multfilm o'chirish")
@admin_router.callback_query(F.data == "admin_del_movie")
async def delete_movie_start(event: Message | CallbackQuery, state: FSMContext):
    if event.from_user.id in ADMINS:
        text = (
            "🗑 <b>Kino/Multfilm o'chirish</b>\n\n"
            "O'chirmoqchi bo'lgan kinoning <b>kodini</b> yozing:\n"
            "Misol: <code>115</code>"
        )
        if isinstance(event, Message):
            await event.answer(text, parse_mode="HTML", reply_markup=back_reply_keyboard())
        else:
            await event.message.answer(text, parse_mode="HTML", reply_markup=back_reply_keyboard())
            await event.answer()
        await state.set_state(MovieState.waiting_for_del_code)

@admin_router.message(MovieState.waiting_for_del_code)
async def process_delete_movie(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        if not message.text:
            return await message.answer("⚠️ Kod yozing.", reply_markup=cancel_keyboard())
        code = message.text.strip()
        movie = await database.get_movie(code)
        if not movie:
            return await message.answer(
                f"❌ <code>{code}</code> kodli kino topilmadi. Boshqa kod kiriting:",
                parse_mode="HTML",
                reply_markup=cancel_keyboard()
            )
        await database.delete_movie(code)
        await state.clear()
        await message.answer(
            f"✅ <b>{movie[2]}</b> (kod: <code>{code}</code>) o'chirildi!",
            parse_mode="HTML",
            reply_markup=admin_reply_keyboard()
        )

# ─── Kanal qo'shish ───────────────────────────────────────────────────────────

@admin_router.message(StateFilter(None), F.text == "➕ Majburiy kanal qo'shish")
@admin_router.callback_query(F.data == "admin_add_channel")
async def add_channel_start(event: Message | CallbackQuery, state: FSMContext, bot: Bot):
    if event.from_user.id in ADMINS:
        channels = await database.get_channels()
        text = "📋 <b>Hozirgi ulangan majburiy kanallar:</b>\n"
        if channels:
            for ch in channels:
                icon = _channel_type_icon(ch)
                # ch[2] is URL, ch[3] is Name, ch[4] is Reward
                text += f"{icon} <b>{ch[3]}</b> — <code>{ch[2]}</code> (Mukofot: {ch[4]:,} so'm)\n"
        else:
            text += "<i>Hozircha hech qanday kanal qo'shilmagan.</i>\n"
        text += "\n<b>Qaysi turdagi kanal qo'shmoqchisiz?</b>"
        
        if isinstance(event, Message):
            await event.answer(text, parse_mode="HTML", reply_markup=channel_type_keyboard())
        else:
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=channel_type_keyboard())
            await event.answer()

@admin_router.callback_query(F.data == "add_chan_telegram")
async def add_chan_telegram(call: CallbackQuery, state: FSMContext):
    if call.from_user.id in ADMINS:
        await call.message.edit_text(
            "📱 <b>Telegram kanal qo'shish</b>\n\n"
            "1️⃣ Botni kanalga admin qiling\n"
            "2️⃣ Kanal username yuboring\n\n"
            "Misol: <code>@CINEMA_uz90</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(ChannelState.waiting_for_channel_id)
        await call.answer()

@admin_router.callback_query(F.data == "add_chan_youtube")
async def add_chan_youtube(call: CallbackQuery, state: FSMContext):
    if call.from_user.id in ADMINS:
        await state.update_data(chan_type="youtube")
        await call.message.edit_text(
            "▶️ <b>YouTube kanal qo'shish</b>\n\n"
            "YouTube kanal havolasini yuboring:\n\n"
            "Misol: <code>https://youtube.com/@kanalnom</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(ChannelState.waiting_for_ext_link)
        await call.answer()

@admin_router.callback_query(F.data == "add_chan_instagram")
async def add_chan_instagram(call: CallbackQuery, state: FSMContext):
    if call.from_user.id in ADMINS:
        await state.update_data(chan_type="instagram")
        await call.message.edit_text(
            "📸 <b>Instagram sahifa qo'shish</b>\n\n"
            "Instagram sahifa havolasini yuboring:\n\n"
            "Misol: <code>https://instagram.com/sahifanom</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(ChannelState.waiting_for_ext_link)
        await call.answer()

@admin_router.message(ChannelState.waiting_for_channel_id)
async def process_channel_id(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id in ADMINS:
        text = message.text.strip()
        try:
            chat = await bot.get_chat(text)
            channel_id = chat.id
            name = chat.title or "Kanal"
            url = f"https://t.me/{chat.username}" if chat.username else None
            if url:
                await state.update_data(channel_id=channel_id, name=name, url=url, chan_type="telegram")
                await message.answer(
                    f"✅ <b>{name}</b> ma'lumotlari olindi.\n\n"
                    "Ushbu kanal uchun <b>mukofot (reward)</b> miqdorini kiriting (so'mda):\n"
                    "Misol: <code>1000</code>",
                    parse_mode="HTML",
                    reply_markup=back_reply_keyboard()
                )
                await state.set_state(ChannelState.waiting_for_channel_reward)
            else:
                await state.update_data(channel_id=channel_id, name=name, chan_type="telegram")
                await message.answer(
                    "⚠️ Kanal yopiq, havolasini yuboring (t.me/... ko'rinishida):",
                    reply_markup=back_reply_keyboard()
                )
                await state.set_state(ChannelState.waiting_for_url)
        except Exception:
            await message.answer(
                "❌ Kanal topilmadi. Username to'g'ri yozdingizmi?\nMisol: <code>@CINEMA_uz90</code>",
                parse_mode="HTML",
                reply_markup=back_reply_keyboard()
            )

@admin_router.message(ChannelState.waiting_for_url)
async def process_channel_url(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        url = message.text.strip()
        await state.update_data(url=url)
        data = await state.get_data()
        await message.answer(
            f"✅ <b>{data['name']}</b> havolasi qabul qilindi.\n\n"
            "Ushbu kanal uchun <b>mukofot (reward)</b> miqdorini kiriting (so'mda):\n"
            "Misol: <code>1000</code>",
            parse_mode="HTML",
            reply_markup=back_reply_keyboard()
        )
        await state.set_state(ChannelState.waiting_for_channel_reward)

@admin_router.message(ChannelState.waiting_for_ext_link)
async def process_ext_link(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        url = message.text.strip()
        data = await state.get_data()
        chan_type = data.get("chan_type", "youtube")
        icon = "▶️" if chan_type == "youtube" else "📸"
        await state.update_data(ext_url=url)
        await message.answer(
            f"{icon} Havola qabul qilindi.\n\n"
            f"Endi kanal/sahifa <b>nomini</b> yozing:\n"
            f"Misol: <code>Cinema UZ Rasmiy</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(ChannelState.waiting_for_ext_name)

@admin_router.message(ChannelState.waiting_for_ext_name)
async def process_ext_name(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        data = await state.get_data()
        chan_type = data.get("chan_type", "youtube")
        name = message.text.strip()
        await state.update_data(name=name)
        
        default_reward = 3000 if chan_type == "youtube" else 2000
        await message.answer(
            f"✅ <b>{name}</b> nomi qabul qilindi.\n\n"
            f"Ushbu sahifa uchun <b>mukofot (reward)</b> miqdorini kiriting (so'mda):\n"
            f"Misol: <code>{default_reward}</code>",
            parse_mode="HTML",
            reply_markup=back_reply_keyboard()
        )
        await state.set_state(ChannelState.waiting_for_channel_reward)

@admin_router.message(ChannelState.waiting_for_channel_reward)
async def process_channel_reward(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        if not message.text or not message.text.isdigit():
            return await message.answer("⚠️ Iltimos, faqat musbat son yozing:")
        
        reward = int(message.text)
        data = await state.get_data()
        import random
        import time as _time
        
        chan_type = data.get("chan_type", "telegram")
        name = data.get("name", "Kanal")
        url = data.get("url") or data.get("ext_url", "")
        channel_id = data.get("channel_id") or (int(_time.time()) + random.randint(1, 1000))
        
        icon = "📱"
        if chan_type == "youtube": icon = "▶️"
        elif chan_type == "instagram": icon = "📸"
        
        result = await database.add_channel(channel_id, url, name, reward)
        await state.clear()
        if result:
            await message.answer(
                f"✅ {icon} <b>{name}</b> qo'shildi!\n"
                f"🔗 Havola: {url}\n"
                f"💰 Mukofot: <b>{reward:,} so'm</b>",
                parse_mode="HTML",
                reply_markup=admin_reply_keyboard()
            )
        else:
            await message.answer(
                "❌ Qo'shishda xatolik. Qaytadan urinib ko'ring.",
                reply_markup=admin_reply_keyboard()
            )

# ─── Kanal o'chirish ──────────────────────────────────────────────────────────

@admin_router.message(StateFilter(None), F.text == "🗑 Kanal o'chirish")
@admin_router.callback_query(F.data == "admin_del_channel")
async def delete_channel_start(event: Message | CallbackQuery, state: FSMContext):
    if event.from_user.id in ADMINS:
        channels = await database.get_channels()
        kb_buttons = []
        for ch in channels:
            icon = _channel_type_icon(ch)
            kb_buttons.append([InlineKeyboardButton(text=f"🗑 {icon} {ch[3]}", callback_data=f"del_chan_{ch[1]}")])
        
        if not kb_buttons:
            msg = "Hech qanday kanal qo'shilmagan."
            if isinstance(event, Message): await event.answer(msg)
            else: await event.message.edit_text(msg, reply_markup=admin_back_button())
            return

        kb_buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_main")])
        markup = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        
        if isinstance(event, Message):
            await event.answer("O'chirmoqchi bo'lgan kanalni tanlang:", reply_markup=markup)
        else:
            await event.message.edit_text("O'chirmoqchi bo'lgan kanalni tanlang:", reply_markup=markup)
            await event.answer()

@admin_router.callback_query(F.data.startswith("del_chan_"))
async def process_delete_channel_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        ch_id = int(call.data.split("_")[2])
        await database.remove_channel(ch_id)
        await call.answer("✅ O'chirildi!")
        await call.message.delete()
        await call.message.answer("✅ Kanal o'chirildi.", reply_markup=admin_reply_keyboard())

# ─── Admin komandalar ─────────────────────────────────────────────────────────

@admin_router.message(Command("balans"))
async def cmd_add_balance(message: Message):
    if message.from_user.id in ADMINS:
        try:
            parts = message.text.split()
            if len(parts) == 3:
                target_id = int(parts[1])
                amount = int(parts[2])
                await database.update_user_balance(target_id, amount)
                await message.answer(f"✅ {target_id} foydalanuvchiga {amount:,} so'm qo'shildi.")
            else:
                await message.answer("Format: /balans ID SUMMA\nMisol: /balans 123456 10000")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")

@admin_router.message(Command("limit"))
async def cmd_add_limit(message: Message):
    if message.from_user.id in ADMINS:
        try:
            parts = message.text.split()
            if len(parts) == 3:
                target_id = int(parts[1])
                lim = int(parts[2])
                await database.update_limit(target_id, lim)
                await message.answer(f"✅ {target_id} foydalanuvchiga limit: {lim} o'rnatildi.")
            else:
                await message.answer("Format: /limit ID SONI\nMisol: /limit 123456 50")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")

@admin_router.message(Command("premium"))
async def cmd_set_premium(message: Message):
    if message.from_user.id in ADMINS:
        try:
            parts = message.text.split()
            if len(parts) == 3:
                target_id = int(parts[1])
                status = parts[2] == "1"
                await database.set_premium(target_id, status)
                await message.answer(f"✅ {target_id} foydalanuvchi premium: {'YOQILDI' if status else 'OCHIRILDI'}")
            else:
                await message.answer("Format: /premium ID 1 (yoqish) yoki 0 (ochirish)")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")

@admin_router.message(Command("user"))
async def cmd_check_user(message: Message):
    if message.from_user.id in ADMINS:
        try:
            parts = message.text.split()
            if len(parts) == 2:
                target_id = int(parts[1])
                user = await database.get_user(target_id)
                if user:
                    premium_st = "Bor ✅" if user[6] else "Yo'q ❌"
                    text = (
                        f"👤 <b>Foydalanuvchi:</b>\n\n"
                        f"🆔 ID: <code>{user[1]}</code>\n"
                        f"👤 Nomi: {user[2]}\n"
                        f"💰 Balans: <b>{user[4]:,}</b> so'm\n"
                        f"🔢 Limit: <b>{user[5]}</b> ta\n"
                        f"💎 Premium: <b>{premium_st}</b>\n"
                        f"🎬 Ko'rilgan: {user[11]} ta\n"
                    )
                    await message.answer(text, parse_mode="HTML")
                else:
                    await message.answer("❌ Foydalanuvchi topilmadi.")
            else:
                await message.answer("Format: /user ID")
        except Exception as e:
            await message.answer(f"Xatolik: {e}")

# ─── Mijozlar inline handlerlari ──────────────────────────────────────────────

@admin_router.callback_query(F.data == "admin_customers")
@admin_router.callback_query(F.data == "admin_add_balance")
async def admin_customers_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        await call.message.edit_text(
            "👥 <b>Mijozlar boshqaruvi bo'limi</b>\n\nPastdagi menyu orqali kerakli bo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=admin_customers_menu()
        )

@admin_router.callback_query(F.data == "admin_search_user")
async def admin_search_user_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id in ADMINS:
        await call.message.answer(
            "🔍 <b>Foydalanuvchi qidirish</b>\n\nFoydalanuvchining <b>ID raqamini</b> yuboring:",
            parse_mode="HTML",
            reply_markup=back_reply_keyboard()
        )
        await state.set_state(AdminState.waiting_for_search_id)
        await call.answer()

@admin_router.message(AdminState.waiting_for_search_id)
async def process_admin_search_id(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        if not message.text or not message.text.isdigit():
            return await message.answer("⚠️ Iltimos, faqat raqamlardan iborat ID yuboring.")
        
        user_id = int(message.text)
        user = await database.get_user(user_id)
        if not user:
            return await message.answer("❌ Bunday ID ga ega foydalanuvchi topilmadi.")
        
        await state.clear()
        # Mocking a callback to reuse view handler
        from aiogram.types import CallbackQuery
        # Simulating callback data for admin_view_user_handler
        class FakeCall:
            def __init__(self, from_user, message, data):
                self.from_user = from_user
                self.message = message
                self.data = data
            async def answer(self, *args, **kwargs): pass

        fake_call = FakeCall(message.from_user, message, f"admin_view_user_{user_id}")
        await admin_view_user_handler(fake_call)

@admin_router.callback_query(F.data.startswith("admin_add_prem_"))
async def admin_add_prem_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        parts = call.data.split("_")
        user_id = int(parts[3])
        months = int(parts[4])
        days = months * 30 if months < 12 else 365
        await database.set_premium(user_id, True, days=days)
        await call.answer(f"✅ {months} oylik premium qo'shildi!", show_alert=True)
        await admin_view_user_handler(call)

@admin_router.callback_query(F.data.startswith("admin_edit_balance_"))
async def admin_edit_balance_callback(call: CallbackQuery, state: FSMContext):
    if call.from_user.id in ADMINS:
        user_id = int(call.data.split("_")[3])
        await state.update_data(target_user_id=user_id)
        await call.message.answer(
            f"💰 <b>ID: {user_id}</b> uchun yangi balans miqdorini kiriting:\n\n"
            f"<i>Masalan: 10000 yoki -5000</i>",
            parse_mode="HTML",
            reply_markup=back_reply_keyboard()
        )
        await state.set_state(AdminState.waiting_for_balance_amount)
        await call.answer()

@admin_router.message(AdminState.waiting_for_balance_amount)
async def process_admin_balance_amount(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        try:
            amount = int(message.text)
            data = await state.get_data()
            user_id = data.get("target_user_id")
            await database.update_user_balance(user_id, amount)
            await state.clear()
            await message.answer(f"✅ ID: {user_id} balansi {amount:+,} so'mga o'zgartirildi.")
            # Qaytadan profilni ko'rsatish
            user = await database.get_user(user_id)
            premium_status = "✅ Ha" if user[6] else "❌ Yo'q"
            text = (
                f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
                f"🆔 ID: <code>{user[1]}</code>\n"
                f"👤 Ism: {user[2]}\n"
                f"💰 Balans: <b>{user[4]:,}</b> so'm\n"
                f"🔢 Limit: <b>{user[5]}</b> ta\n\n"
                f"💎 Premium: <b>{premium_status}</b>\n"
            )
            await message.answer(text, parse_mode="HTML", reply_markup=admin_user_manage_keyboard(user[1], user[6]))
        except ValueError:
            await message.answer("⚠️ Iltimos, son kiriting.")

@admin_router.callback_query(F.data == "admin_main")
async def admin_main_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        await call.message.edit_text("Admin paneliga qaytdingiz.")
        await call.message.answer("Admin paneli:", reply_markup=admin_reply_keyboard())

@admin_router.callback_query(F.data.startswith("admin_list_"))
async def admin_list_users_handler(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        parts = call.data.split("_")
        list_type = parts[2]
        page = int(parts[3]) if len(parts) > 3 else 0
        limit = 10
        offset = page * limit

        users, total = [], 0
        title = ""

        if list_type == "premium":
            users_all = await database.get_active_premiums()
            total = len(users_all)
            users = users_all[offset:offset+limit]
            title = "🌟 <b>Aktiv premium foydalanuvchilar:</b>"
        elif list_type == "expired":
            users_all = await database.get_expired_premiums()
            total = len(users_all)
            users = users_all[offset:offset+limit]
            title = "⏳ <b>Muddati tugagan premiumlar:</b>"
        else:
            users_list, total_count = await database.get_users_paged(offset, limit)
            users = users_list
            total = total_count
            title = "👥 <b>Barcha foydalanuvchilar:</b>"

        if not users and page == 0:
            return await call.answer("Ro'yxat bo'sh!", show_alert=True)

        total_pages = max(1, (total + limit - 1) // limit)
        await call.message.edit_text(
            f"{title}\n\nJami: {total} ta\nSahifa: {page + 1}/{total_pages}",
            parse_mode="HTML",
            reply_markup=admin_user_list_keyboard(users, page, total_pages, list_type)
        )

@admin_router.callback_query(F.data.startswith("admin_view_user_"))
async def admin_view_user_handler(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        user_id = int(call.data.split("_")[3])
        user = await database.get_user(user_id)
        if not user:
            return await call.answer("Foydalanuvchi topilmadi!", show_alert=True)
        premium_status = "✅ Ha" if user[6] else "❌ Yo'q"
        text = (
            f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
            f"🆔 ID: <code>{user[1]}</code>\n"
            f"👤 Ism: {user[2]}\n"
            f"💰 Balans: <b>{user[4]:,}</b> so'm\n"
            f"🔢 Limit: <b>{user[5]}</b> ta\n\n"
            f"💎 Premium: <b>{premium_status}</b>\n"
        )
        if user[6]:
            expiry_val = str(user[8]).split('.')[0] if user[8] else "Noaniq"
            text += f"📅 Tugash muddati: <code>{expiry_val}</code>\n"
        text += f"\n📅 Qo'shilgan: {str(user[9]).split('.')[0]}\n"
        text += f"🎬 Ko'rilgan kinolar: {user[11]} ta"
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_user_manage_keyboard(user[1], user[6]))

@admin_router.callback_query(F.data.startswith("admin_give_limit_"))
async def admin_give_limit_handler(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        user_id = int(call.data.split("_")[3])
        await call.message.edit_text(
            f"🔢 <b>{user_id}</b> uchun limit miqdorini tanlang:",
            reply_markup=admin_limit_give_keyboard(user_id)
        )

@admin_router.callback_query(F.data.startswith("admin_set_limit_"))
async def admin_set_limit_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        parts = call.data.split("_")
        user_id = int(parts[3])
        amount = int(parts[4])
        async with aiosqlite.connect(database.DB_NAME) as db:
            await db.execute("UPDATE users SET limit_count = limit_count + ? WHERE telegram_id = ?", (amount, user_id))
            await db.commit()
        await call.answer(f"✅ {amount} ta limit qo'shildi!", show_alert=True)
        await admin_view_user_handler(call)

@admin_router.callback_query(F.data.startswith("admin_toggle_prem_"))
async def admin_toggle_prem_callback(call: CallbackQuery):
    if call.from_user.id in ADMINS:
        parts = call.data.split("_")
        user_id = int(parts[3])
        status = parts[4] == "1"
        await database.set_premium(user_id, status)
        await call.answer(f"✅ Premium: {'Yoqildi' if status else 'Ochirildi'}", show_alert=True)
        await admin_view_user_handler(call)

# ─── To'lov tasdiqlash/rad etish ─────────────────────────────────────────────

@admin_router.callback_query(F.data.startswith("approve_app_"))
async def approve_payment(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id in ADMINS:
        app_id = int(callback.data.split("_")[2])
        app = await database.get_application(app_id)
        if app:
            user_id = app[1]
            app_type = app[5]
            amount = app[6]
            months = app[4]

            if app_type == 'PREMIUM':
                days = months * 30 if months < 12 else 365
                await database.set_premium(user_id, True, days)
                user_info = await database.get_user(user_id)
                expiry = user_info[8]
                expiry_str = str(expiry).split('.')[0] if expiry else "Noma'lum"
                plan_text = f"{months} oylik" if months < 12 else "1 yillik"
                notify_text = (
                    f"🎊 <b>Tabriklaymiz!</b>\n\nSizning to'lovingiz tasdiqlandi.\n"
                    f"Premium status <b>{plan_text}</b>ga faollashtirildi.\n"
                    f"📅 Amal qilish muddati: {expiry_str} gacha."
                )
                summary_text = f"✅ <b>TASDIQLANDI (Premium {plan_text})</b>"
            elif app_type == 'LIMIT':
                # Limit summasiga qarab coin qo'shamiz (5 coin = LIMIT_PRICE)
                from config import LIMIT_PRICE
                coin_amount = max(5, (amount // LIMIT_PRICE) * 5) if LIMIT_PRICE > 0 else 5
                async with aiosqlite.connect(database.DB_NAME) as db:
                    await db.execute(
                        "UPDATE users SET limit_count = limit_count + ? WHERE telegram_id = ?",
                        (coin_amount, user_id)
                    )
                    await db.commit()
                notify_text = (
                    f"🎊 <b>Tabriklaymiz!</b>\n\nSizning to'lovingiz tasdiqlandi.\n"
                    f"Hisobingizga <b>{coin_amount} ta coin limiti</b> qo'shildi! 🎬"
                )
                summary_text = f"✅ <b>TASDIQLANDI ({coin_amount} ta coin qo'shildi)</b>"
            else:
                # BALANCE
                await database.update_user_balance(user_id, amount)
                notify_text = (
                    f"✅ <b>Tabriklaymiz!</b>\n\nSizning to'lovingiz tasdiqlandi.\n"
                    f"Balansingizga <b>{amount:,} so'm</b> qo'shildi."
                )
                summary_text = f"✅ <b>TASDIQLANDI (Balans +{amount:,})</b>"

            await database.update_application_status(app_id, 'APPROVED')
            try:
                await bot.send_message(user_id, notify_text, parse_mode="HTML")
            except Exception as e:
                print(f"Error sending msg to user: {e}")
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n{summary_text}", parse_mode="HTML"
            )
        await callback.answer("Tasdiqlandi!")

@admin_router.callback_query(F.data.startswith("reject_app_"))
async def reject_payment(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id in ADMINS:
        app_id = int(callback.data.split("_")[2])
        app = await database.get_application(app_id)
        if app:
            await database.update_application_status(app_id, 'REJECTED')
            try:
                await bot.send_message(
                    app[1],
                    "❌ Kechirasiz, siz yuborgan to'lov cheki rad etildi. Iltimos adminga murojaat qiling."
                )
            except:
                pass
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n❌ <b>RAD ETILDI</b>", parse_mode="HTML"
            )
        await callback.answer("Rad etildi!")
