from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter

import database
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
import time
import urllib.parse

class UserState(StatesGroup):
    waiting_for_screenshot = State()
    waiting_for_search_query = State()
    waiting_for_custom_limit = State()
    waiting_for_top_up_amount = State()

from keyboards.inline import (
    profile_keyboard, admin_approval_keyboard, premium_plans_keyboard,
    premium_payment_keyboard, premium_auto_keyboard, premium_confirm_keyboard,
    premium_balance_confirm_keyboard, limit_payment_keyboard, limit_auto_keyboard,
    get_earning_keyboard, get_subscription_keyboard, user_back_button, user_cancel_keyboard
)
from keyboards.reply import main_reply_keyboard, back_reply_keyboard
from config import LIMIT_PRICE, ADMINS, LOGO_PATH, PAYMENT_LINKS, ADMIN_CARD, ADMIN_CARD_NAME, BOT_NAME

user_router = Router()
    
INITIAL_CHANNELS = [
    {"url": "https://t.me/GAMINGPRO2025", "username": "@GAMINGPRO2025", "name": "GAMINGPRO2025", "type": "telegram", "reward": 0, "icon": "📱"},
    {"url": "https://t.me/MERCYRE2025", "username": "@MERCYRE2025", "name": "MERCYRE2025", "type": "telegram", "reward": 0, "icon": "📱"},
    {"url": "https://t.me/CINEMA_uz90", "username": "@CINEMA_uz90", "name": "CINEMA_uz90", "type": "telegram", "reward": 0, "icon": "📱"},
    {"url": "https://www.instagram.com/cybergames2024/", "name": "cybergames2024", "type": "instagram", "reward": 0, "icon": "📸"},
    {"url": "https://www.instagram.com/cinema_uzb90/", "name": "cinema_uzb90", "type": "instagram", "reward": 0, "icon": "📸"},
    {"url": "https://www.youtube.com/@MERCYRE2024", "name": "MERCYRE2024", "type": "youtube", "reward": 0, "icon": "▶️"},
]


def _limit_price_for_coin(coin_amount: int) -> int:
    # LIMIT_PRICE bazaviy paket: 5 coin
    return (coin_amount // 5) * LIMIT_PRICE


def _build_safopay_url(price: int, user_id: int, note: str = "") -> str | None:
    # Har bir summa uchun alohida SafoPay link bo'lishi kerak.
    # Noto'g'ri fallback oldini olish uchun aynan narx bo'yicha link topilmasa None qaytaramiz.
    base_url = PAYMENT_LINKS.get(price)
    if not base_url:
        return None
    order_id = f"{user_id}_{int(time.time())}"
    params = {
        "order_id": order_id,
        # SafoPay amount ni so'm formatida kutadi (15000), tiyin emas.
        "amount": int(price),
        "comment": note or f"{BOT_NAME} {price} som",
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


@user_router.callback_query(F.data == "cancel_user_action")
@user_router.message(F.text == "⬅️ Orqaga qaytish")
async def process_cancel_user_action(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    msg = "🏠 Asosiy menyuga qaytdingiz."
    if isinstance(event, CallbackQuery):
        await event.message.answer(msg, reply_markup=main_reply_keyboard())
        await event.answer()
    else:
        await event.answer(msg, reply_markup=main_reply_keyboard())


@user_router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    await database.add_user(user_id, message.from_user.full_name)
    await database.check_and_update_premium(user_id)
    
    # Obuna tekshiruvi (Ham hamma foydalanuvchilar, ham Adminlar uchun testimiz uchun)
    user_data = await database.get_user(user_id)
    is_premium = user_data[6] if user_data else False
    
    db_channels = await database.get_channels()
    unsubscribed_tg = []
    all_tg_channels = []
    all_ext_channels = []
    
    # Initial channels
    for ch in INITIAL_CHANNELS:
        if ch["type"] == "telegram":
            all_tg_channels.append({"chat_id": ch["username"], "url": ch["url"], "name": ch["name"]})
        else:
            all_ext_channels.append({"url": ch["url"], "name": ch["name"]})
            
    # DB channels
    for ch in db_channels:
        if ch[1] < 0: # TG
            if not any(x["chat_id"] == ch[1] for x in all_tg_channels):
                all_tg_channels.append({"chat_id": ch[1], "url": ch[2], "name": ch[3]})
        else:
            if not any(x["url"] == ch[2] for x in all_ext_channels):
                all_ext_channels.append({"url": ch[2], "name": ch[3]})

    # Tekshiruv
    for ch in all_tg_channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                unsubscribed_tg.append(ch)
        except:
            unsubscribed_tg.append(ch)
    
    if unsubscribed_tg and not is_premium:
        welcome_text = (
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart!\n"
            "💰 Kanallarga obuna bo'lib pul ishlashingiz ham mumkin!"
        )
        keyboard = get_subscription_keyboard(unsubscribed_tg, all_ext_channels)
        try:
            logo = FSInputFile(LOGO_PATH)
            await message.answer_photo(logo, caption=welcome_text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await message.answer(welcome_text, parse_mode="HTML", reply_markup=keyboard)
        return

    # Agar hammasi OK bo'lsa yoki Premium bo'lsa
    # Admin bo'lsa admin panelini chiqarish (bu yerga faqat obuna OK bo'lsa keladi)
    if user_id in ADMINS:
        from keyboards.reply import admin_reply_keyboard
        await message.answer(
            f"Salom, Admin {message.from_user.full_name}!\nAdministratsiya paneliga xush kelibsiz.",
            reply_markup=admin_reply_keyboard()
        )
        return

    await send_welcome_message(message)

async def send_welcome_message(message: Message):
    welcome_text = (
        "🎬 <b>CINEMA_uz90_bot — Sevimli kinolaringiz markazi!</b>\n\n"
        "Bu bot orqali siz:\n"
        "🔹 Eng so'nggi dunyo premyera kinolarni;\n"
        "🔹 Sevimli va qiziqarli multifilmlarni;\n"
        "🔹 O'zbek tilidagi sifatli filmlarni tomosha qilishingiz mumkin.\n\n"
        "🍿 <b>Botga obuna bo'ling va eng sara kontentlardan bahramand bo'ling!</b>\n\n"
        "📢 Rasmiy kanal: @CINEMA_uz90\n"
        "👤 Admin: @XONaction\n\n"
        "👇 <b>Botni davom ettirish uchun kanaldagi kino kodini yuboring!</b>"
    )
    from config import LOGO_PATH
    from keyboards.reply import main_reply_keyboard
    from aiogram.types import FSInputFile
    try:
        logo = FSInputFile(LOGO_PATH)
        await message.answer_photo(logo, caption=welcome_text, parse_mode="HTML", reply_markup=main_reply_keyboard())
    except:
        await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_reply_keyboard())


@user_router.message(F.text == "👤 Profil")
async def cmd_profile(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    await database.add_user(message.from_user.id, message.from_user.full_name)
    await database.check_and_update_premium(message.from_user.id)
    user = await database.get_user(message.from_user.id)
    if not user:
        return await message.answer("Siz haqingizda ma'lumot topilmadi.")
    tg_id = user[1]
    fname = user[2]
    balance = user[4]
    l_count = user[5]
    is_prem = user[6]
    p_end = user[8]

    # Telegram kanallar bo'yicha real obuna holatini chiqaramiz
    db_channels = await database.get_channels()
    tg_channels = []
    subscribed_names = []
    for ch in db_channels:
        if ch[1] < 0:
            tg_channels.append({"chat_id": ch[1], "name": ch[3]})
    for ch in tg_channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=message.from_user.id)
            if member.status in ["member", "administrator", "creator"]:
                subscribed_names.append(ch["name"])
        except Exception:
            # Kanal tekshirib bo'lmasa, obuna bo'lgan deb hisoblamaymiz
            pass

    premium_until = str(p_end).split('.')[0] if (is_prem and p_end) else "Mavjud emas"
    sub_count = f"{len(subscribed_names)}/{len(tg_channels)}"
    sub_lines = "\n".join(f"• {name}" for name in subscribed_names[:10]) if subscribed_names else "• Hozircha yo'q"
    if len(subscribed_names) > 10:
        sub_lines += "\n• ..."

    profile_text = (
        f"👤 <b>Mening profilim</b>\n\n"
        f"🆔 ID: <code>{tg_id}</code>\n"
        f"👤 Ism-familiya: <b>{fname}</b>\n"
        f"💵 Mavjud coin': <b>{l_count if not is_prem else 'Cheksiz'}</b>\n"
        f"💰 Balans: <b>{balance:,}</b> so'm\n"
        f"💎 Premium: <b>{'Faol ✅' if is_prem else 'Faol emas ❌'}</b>\n"
        f"📅 Premium tugash vaqti: <b>{premium_until}</b>\n\n"
        f"📢 Obuna bo'lgan kanallar soni: <b>{sub_count}</b>\n"
        f"{sub_lines}\n\n"
        f"<i>Balans va premium bo'yicha amallar uchun pastdagi tugmalardan foydalaning.</i>"
    )
    try:
        logo = FSInputFile(LOGO_PATH)
        await message.answer_photo(logo, caption=profile_text, parse_mode="HTML", reply_markup=profile_keyboard())
    except:
        await message.answer(profile_text, parse_mode="HTML", reply_markup=profile_keyboard())


@user_router.message(F.text == "💰 Balans")
async def cmd_balance(message: Message, state: FSMContext):
    await state.clear()
    await database.add_user(message.from_user.id, message.from_user.full_name)
    await database.check_and_update_premium(message.from_user.id)
    user = await database.get_user(message.from_user.id)
    if not user:
        return await message.answer("Siz haqingizda ma'lumot topilmadi.")
    balance = user[4]
    spent = await database.get_user_spent_amount(message.from_user.id)
    premium_until = str(user[8]).split('.')[0] if (user[6] and user[8]) else "Mavjud emas"
    text = (
        f"💰 <b>Sizning balansingiz:</b>\n\n"
        f"💵 Mavjud coin': <b>{user[5] if not user[6] else 'Cheksiz'}</b>\n"
        f"💸 Mavjud mablag': <b>{balance:,}</b> so'm\n"
        f"📉 Jami sarflangan mablag': <b>{spent:,}</b> so'm\n"
        f"💎 Premium obuna vaqti: <b>{premium_until}</b>\n\n"
        f"<i>To'lov/premium uchun '👤 Profil' bo'limiga o'ting.</i>"
    )
    try:
        logo = FSInputFile(LOGO_PATH)
        await message.answer_photo(logo, caption=text, parse_mode="HTML", reply_markup=user_back_button())
    except:
        await message.answer(text, parse_mode="HTML", reply_markup=user_back_button())


@user_router.message(F.text == "🎬 Izlash")
async def cmd_search_start(message: Message, state: FSMContext):
    await message.answer(
        "🎬 <b>Kino kodini yoki nomini yuboring:</b>\n\nMasalan: <code>113</code>",
        parse_mode="HTML",
        reply_markup=back_reply_keyboard()
    )
    await state.set_state(UserState.waiting_for_search_query)


@user_router.message(F.text == "✍️ Adminga murojaat")
async def cmd_contact_admin(message: Message):
    from config import ADMIN_USER
    await message.answer(f"🆘 Muammo yuzaga kelsa yoki balansni to'ldirmoqchi bo'lsangiz, adminga yozing: {ADMIN_USER}", reply_markup=user_back_button())


@user_router.callback_query(F.data == "contact_admin")
async def callback_contact_admin(callback: CallbackQuery):
    from config import ADMIN_USER
    await callback.message.answer(f"🆘 Adminga murojaat: {ADMIN_USER}")
    await callback.answer()


# ─── PREMIUM OQIMI ────────────────────────────────────────────────────────────

@user_router.callback_query(F.data == "show_premium")
async def process_show_premium(callback: CallbackQuery):
    text = (
        "💎 <b>Premium obuna</b>\n\n"
        "Premium orqali quyidagilarga ega bo'lasiz:\n"
        "• Kanallarga obuna bo'lmasdan kino ko'rish\n"
        "• Reklamasiz foydalanish\n"
        "• Cheksiz kino ko'rish\n\n"
        "📋 <b>Quyidagi tariflardan birini tanlang:</b>"
    )
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=premium_plans_keyboard())
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=premium_plans_keyboard())
    await callback.answer()


@user_router.callback_query(F.data.startswith("select_prem_"))
async def process_select_plan(callback: CallbackQuery):
    months = int(callback.data.split("_")[2])
    prices = {1: 15000, 3: 35000, 12: 65000}
    price = prices.get(months, 15000)
    days = months * 30 if months < 12 else 365
    name = f"{months} oylik obuna" if months < 12 else "1 yillik obuna"
    text = (
        "💳 <b>To'lov tizimini tanlang</b>\n\n"
        f"💎 Tarif: {name}\n"
        f"📅 Muddat: {days} kun\n"
        f"💰 Narx: <b>{price:,} so'm</b>"
    )
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=premium_payment_keyboard(months))
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=premium_payment_keyboard(months))
    await callback.answer()


@user_router.callback_query(F.data.startswith("method_prem_"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    months = int(parts[2])
    method = parts[3]
    prices = {1: 15000, 3: 35000, 12: 65000}
    price = prices.get(months, 15000)
    days = months * 30 if months < 12 else 365
    name = f"{months} oylik obuna" if months < 12 else "1 yillik obuna"

    if method == "auto":
        await callback.answer("ℹ️ Onlayn Payme/Click o'chirilgan. Karta yoki balansdan to'lang.", show_alert=True)
        return

    elif method == "manual":
        # Karta orqali manual to'lov
        order_id = f"{callback.from_user.id}_{int(time.time())}"
        await state.update_data(app_type='PREMIUM', selected_months=months, amount=price)
        text = (
            "🏧 <b>Karta / Bank o'tkazmasi orqali to'lov</b>\n\n"
            f"📦 Tarif: <b>{name}</b>\n"
            f"📅 Muddat: {days} kun\n"
            f"💰 To'lov summasi: <b>{price:,} so'm</b>\n\n"
            f"💳 Karta raqami: <code>{ADMIN_CARD}</code>\n"
            f"👤 Karta egasi: <b>{ADMIN_CARD_NAME}</b>\n\n"
            f"📌 Izoh (comment) ga: <code>{order_id}</code>\n\n"
            "✅ To'lov qilganingizdan so'ng chekni yuboring."
        )
        kb = premium_confirm_keyboard(months)
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

    elif method == "balance":
        # Balansdan to'lash
        user = await database.get_user(callback.from_user.id)
        balance = user[4]
        if balance >= price:
            text = (
                "💰 <b>Balansdan to'lash</b>\n\n"
                f"📦 Tarif: <b>{name}</b>\n"
                f"📅 Muddat: {days} kun\n"
                f"💰 Narx: <b>{price:,} so'm</b>\n"
                f"💵 Sizning balansingiz: <b>{balance:,} so'm</b>\n\n"
                "Tasdiqlaysizmi? Balansdan ushlab qolinadi."
            )
            kb = premium_balance_confirm_keyboard(months)
        else:
            text = (
                "❌ <b>Balansingizda mablag' yetarli emas!</b>\n\n"
                f"💰 Kerak: <b>{price:,} so'm</b>\n"
                f"💵 Mavjud: <b>{balance:,} so'm</b>\n\n"
                "Karta orqali to'lash yoki balansni to'ldiring."
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏧 Karta orqali", callback_data=f"method_prem_{months}_manual")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"select_prem_{months}")]
            ])
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

    await callback.answer()


@user_router.callback_query(F.data.startswith("buy_prem_"))
async def process_buy_premium_balance(callback: CallbackQuery, state: FSMContext):
    """Balansdan premium sotib olish (buy_prem_{months}_balance)"""
    parts = callback.data.split("_")
    months = int(parts[2])
    prices = {1: 15000, 3: 35000, 12: 65000}
    price = prices.get(months, 15000)
    days = months * 30 if months < 12 else 365
    name = f"{months} oylik" if months < 12 else "1 yillik"

    user = await database.get_user(callback.from_user.id)
    balance = user[4]

    if user[6]:
        await callback.answer("💎 Sizda premium allaqachon faollashtirilgan!", show_alert=True)
        return

    if balance >= price:
        await database.update_user_balance(callback.from_user.id, -price)
        await database.set_premium(callback.from_user.id, True, days=days)
        await state.clear()
        user_after = await database.get_user(callback.from_user.id)
        expiry_str = str(user_after[8]).split('.')[0] if user_after[8] else "Noma'lum"
        text = (
            f"🎊 <b>Tabriklaymiz!</b>\n\n"
            f"Siz <b>{name} Premium</b> foydalanuvchiga aylandingiz!\n"
            f"📅 Muddat: {expiry_str} gacha\n\n"
            f"Endi barcha kinolar siz uchun cheksiz! 🎬"
        )
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, parse_mode="HTML")
    else:
        await callback.answer("❌ Balansingizda mablag' yetarli emas!", show_alert=True)
    await callback.answer()


@user_router.callback_query(F.data.startswith("send_screenshot_"))
async def process_send_screenshot_tiered(callback: CallbackQuery, state: FSMContext):
    months = int(callback.data.split("_")[2])
    prices = {1: 15000, 3: 35000, 12: 65000}
    price = prices.get(months, 15000)
    await state.update_data(app_type='PREMIUM', selected_months=months, amount=price)
    await callback.message.answer(
        "📸 <b>To'lov chekini yuboring</b>\n\n"
        "Chekni rasm (screenshot) ko'rinishida yuboring.\n"
        "Admin tekshirib, premium faollashtiradi. ✅",
        parse_mode="HTML"
    )
    await state.set_state(UserState.waiting_for_screenshot)
    await callback.answer()


# ─── LIMIT (KOIN) SOTIB OLISH ─────────────────────────────────────────────────

@user_router.callback_query(F.data == "buy_limit")
async def process_buy_limit_options(callback: CallbackQuery):
    """Limit sotib olish — coin paketi tanlash"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5 coin — 5,000 so'm", callback_data="buy_limit_pack_5")],
        [InlineKeyboardButton(text="20 coin — 20,000 so'm", callback_data="buy_limit_pack_20")],
        [InlineKeyboardButton(text="🔢 Boshqa miqdor", callback_data="buy_limit_custom")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_profile")]
    ])
    text = (
        "🎫 <b>Limit sotib olish</b>\n\n"
        "Kerakli coin paketini tanlang:"
    )
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=kb)
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@user_router.callback_query(F.data == "buy_limit_custom")
async def process_buy_limit_custom(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔢 <b>Necha limit (coin) sotib olmoqchisiz?</b>\n\n"
        "Shunchaki sonni yozib yuboring (Masalan: 15).\n"
        "<i>Eslatma: 5 coin = 5,000 so'm</i>\n\n"
        "Bekor qilish uchun ⬅️ Orqaga qaytish tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=back_reply_keyboard()
    )
    await state.set_state(UserState.waiting_for_custom_limit)
    await callback.answer()

@user_router.message(UserState.waiting_for_custom_limit)
async def process_custom_limit_input(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "⬅️ Orqaga qaytish":
        return await process_cancel_user_action(message, state)
    if not message.text or not message.text.isdigit():
        return await message.answer("⚠️ Iltimos, faqat musbat son yozing:")
    
    coin_amount = int(message.text)
    if coin_amount < 1:
        return await message.answer("⚠️ Minimal 1 ta coin sotib olish mumkin.")
    
    # Narxni hisoblash: 5 coin = 5000 som -> 1 coin = 1000 som
    amount = coin_amount * 1000
    
    await state.update_data(selected_limit_coins=coin_amount, amount=amount, app_type='LIMIT')
    
    text = (
        "🎫 <b>Limit sotib olish</b>\n\n"
        f"{coin_amount} ta coin limiti narxi: <b>{amount:,} so'm</b>\n\n"
        "Qanday to'lash usulini tanlang:"
    )
    kb = limit_payment_keyboard(coin_amount)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)
    await state.set_state(None)

@user_router.callback_query(F.data.startswith("buy_limit_pack_"))
async def process_buy_limit_pack(callback: CallbackQuery):
    coin_amount = int(callback.data.split("_")[3])
    amount = _limit_price_for_coin(coin_amount)
    text = (
        "🎫 <b>Limit sotib olish</b>\n\n"
        f"{coin_amount} ta coin limiti narxi: <b>{amount:,} so'm</b>\n\n"
        "Qanday to'lash usulini tanlang:"
    )
    kb = limit_payment_keyboard(coin_amount)
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=kb)
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@user_router.callback_query(F.data == "buy_limit_card")
async def process_buy_limit_card(callback: CallbackQuery, state: FSMContext):
    """Eski callback: Payme/Click o'chirilgan."""
    await callback.answer("ℹ️ Onlayn Payme/Click o'chirilgan. Karta yoki balansdan to'lang.", show_alert=True)
    return


@user_router.callback_query(F.data.startswith("buy_limit_manual_"))
async def process_buy_limit_manual(callback: CallbackQuery, state: FSMContext):
    """Limit — karta/bank orqali manual to'lash"""
    coin_amount = int(callback.data.split("_")[3])
    amount = _limit_price_for_coin(coin_amount)
    await state.update_data(app_type='LIMIT', amount=amount, selected_months=0, selected_limit_coins=coin_amount)
    text = (
        "🏧 <b>Karta / Bank o'tkazmasi orqali to'lov</b>\n\n"
        f"📦 Mahsulot: {coin_amount} ta coin limiti\n"
        f"💰 To'lov summasi: <b>{amount:,} so'm</b>\n\n"
        f"💳 Karta: <code>{ADMIN_CARD}</code>\n"
        f"👤 Egasi: <b>{ADMIN_CARD_NAME}</b>\n\n"
        "✅ To'lov qilgach, «Men to'ladim — chekni yuborish» tugmasini bosing."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Men to'ladim — chekni yuborish", callback_data="send_limit_screenshot")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"buy_limit_pack_{coin_amount}")]
    ])
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@user_router.callback_query(F.data == "send_limit_screenshot")
async def process_send_limit_screenshot(callback: CallbackQuery, state: FSMContext):
    """Limit uchun chek yuborish holatiga o'tish"""
    data = await state.get_data()
    coin_amount = int(data.get("selected_limit_coins", 5))
    amount = int(data.get("amount", _limit_price_for_coin(coin_amount)))
    await state.update_data(app_type='LIMIT', amount=amount, selected_months=0, selected_limit_coins=coin_amount)
    await callback.message.answer(
        "📸 <b>To'lov chekini yuboring</b>\n\n"
        "Chekni rasm (screenshot) ko'rinishida yuboring.\n"
        "Admin tekshirib, limitingizni qo'shadi. ✅",
        parse_mode="HTML"
    )
    await state.set_state(UserState.waiting_for_screenshot)
    await callback.answer()


@user_router.callback_query(F.data.startswith("buy_limit_balance_"))
async def process_buy_limit_balance(callback: CallbackQuery):
    """Limit — Balansdan to'lash"""
    coin_amount = int(callback.data.split("_")[3])
    amount = _limit_price_for_coin(coin_amount)
    user = await database.get_user(callback.from_user.id)
    balance = user[4]
    if balance >= amount:
        await database.update_user_balance(callback.from_user.id, -amount)
        new_limit = user[5] + coin_amount
        await database.update_limit(callback.from_user.id, new_limit)
        text = (
            f"✅ <b>Muvaffaqiyatli!</b>\n\n"
            f"{coin_amount} ta coin limiti qo'shildi!\n"
            f"Joriy limit: <b>{new_limit}</b> ta"
        )
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, parse_mode="HTML")
    else:
        text = (
            f"❌ <b>Balansingizda mablag' yetarli emas!</b>\n\n"
            f"💰 Kerak: <b>{amount:,} so'm</b>\n"
            f"💵 Mavjud: <b>{balance:,} so'm</b>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏧 Karta orqali to'lash", callback_data=f"buy_limit_manual_{coin_amount}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"buy_limit_pack_{coin_amount}")]
        ])
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


# ─── BALANS TO'LDIRISH ────────────────────────────────────────────────────────

@user_router.callback_query(F.data == "top_up_balance")
async def process_top_up_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "💰 <b>Qancha miqdorda balansni to'ldirmoqchisiz?</b>\n\n"
        "Shunchaki summani so'mda yuboring (Masalan: 10000).\n\n"
        "Bekor qilish uchun ⬅️ Orqaga qaytish tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=back_reply_keyboard()
    )
    await state.set_state(UserState.waiting_for_top_up_amount)
    await callback.answer()

@user_router.message(UserState.waiting_for_top_up_amount)
async def process_top_up_amount_input(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "⬅️ Orqaga qaytish":
        return await process_cancel_user_action(message, state)
    if not message.text or not message.text.isdigit():
        return await message.answer("⚠️ Iltimos, faqat musbat son yozing (Masalan: 15000):")
    
    amount = int(message.text)
    if amount < 1000:
        return await message.answer("⚠️ Minimal to'lov miqdori 1,000 so'm.")
    
    order_id = f"{message.from_user.id}_{int(time.time())}"
    await state.update_data(app_type='BALANCE', amount=amount)
    
    text = (
        "💰 <b>Balansni to'ldirish</b>\n\n"
        f"📦 Buyurtma ID: <code>#{order_id}</code>\n"
        f"💰 To'lov summasi: <b>{amount:,} so'm</b>\n\n"
        f"💳 Karta: <code>{ADMIN_CARD}</code>\n"
        f"👤 Egasi: <b>{ADMIN_CARD_NAME}</b>\n\n"
        f"☝️ Izohga (comment): <code>{order_id}</code>\n\n"
        "⚠️ To'lov qilgandan so'ng chekni yuboring."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Chekni yuborish", callback_data="send_screenshot")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_profile")]
    ])
    try:
        logo = FSInputFile(LOGO_PATH)
        await message.answer_photo(logo, caption=text, parse_mode="HTML", reply_markup=kb)
    except:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
    await state.set_state(None)


@user_router.callback_query(F.data == "send_screenshot")
async def process_send_screenshot_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Iltimos, to'lov chekini (rasm ko'rinishida) yuboring:")
    await state.set_state(UserState.waiting_for_screenshot)
    await callback.answer()


@user_router.callback_query(F.data == "show_profile")
async def callback_show_profile(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    await cmd_profile(callback.message, state, callback.bot)
    await callback.answer()

@user_router.callback_query(F.data == "close_menu")
async def process_close_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer("Menyu yopildi.")

@user_router.callback_query(F.data == "show_main_menu")
async def process_show_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except:
        pass
    await send_welcome_message(callback.message)
    await callback.answer()


# ─── CHEK QABUL QILISH ────────────────────────────────────────────────────────

@user_router.message(UserState.waiting_for_screenshot, F.photo)
async def process_screenshot_received(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    app_type = data.get("app_type", "PREMIUM")
    months = data.get("selected_months", 1)
    amount = data.get("amount", 0)
    photo_id = message.photo[-1].file_id

    app_id = await database.add_application(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        photo_id=photo_id,
        plan_months=months,
        app_type=app_type,
        amount=amount
    )
    await state.clear()
    await message.answer(
        "✅ <b>Chek qabul qilindi!</b>\n\n"
        "📩 Sizning arizangiz adminlarga yuborildi va <b>24/7</b> ko'rib chiqiladi.\n"
        "Ko'rib chiqilgach sizga <b>tasdiqlandi</b> yoki <b>rad etildi</b> degan xabar yuboriladi. ⏳",
        parse_mode="HTML"
    )

    if app_type == 'PREMIUM':
        type_text = "💎 PREMIUM"
        detail = f"{months} oylik / {amount:,} so'm"
    elif app_type == 'LIMIT':
        limit_coins = data.get("selected_limit_coins", max(5, (amount // LIMIT_PRICE) * 5))
        type_text = f"🎫 LIMIT ({limit_coins} ta coin)"
        detail = f"{amount:,} so'm"
    else:
        type_text = "💰 BALANS"
        detail = f"{amount:,} so'm"

    for admin_id in ADMINS:
        try:
            await bot.send_photo(
                admin_id,
                photo=photo_id,
                caption=(
                    f"📩 <b>Yangi to'lov cheki!</b>\n\n"
                    f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
                    f"🆔 ID: <code>{message.from_user.id}</code>\n"
                    f"📂 Turi: <b>{type_text}</b>\n"
                    f"💵 Ma'lumot: <b>{detail}</b>\n\n"
                    f"Tasdiqlaysizmi?"
                ),
                parse_mode="HTML",
                reply_markup=admin_approval_keyboard(app_id=app_id)
            )
        except Exception as e:
            print(f"Admin notify error: {e}")


# ─── QIDIRUV ─────────────────────────────────────────────────────────────────

@user_router.message(UserState.waiting_for_search_query)
async def process_search_query(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        return
    if message.text.strip() == "⬅️ Orqaga qaytish":
        return await process_cancel_user_action(message, state)
    await state.clear()
    query = message.text.strip()
    user = await database.get_user(message.from_user.id)
    is_admin = message.from_user.id in ADMINS
    if not user:
        await database.add_user(message.from_user.id, message.from_user.full_name)
        user = await database.get_user(message.from_user.id)
    l_count = user[5]
    is_prem = user[6]
    if not is_prem and l_count <= 0 and not is_admin:
        return await message.answer("❌ Limitingiz tugadi. Profil bo'limidan limit sotib oling yoki Premium oling.")
    if query.startswith("/kod_"):
        query = query.replace("/kod_", "")
    if query.isdigit():
        movie = await database.get_movie(query)
        if movie:
            await send_movie_response(message, bot, movie, is_admin)
        else:
            await message.answer("❌ Bunday kodli kino botda mavjud emas.")
    else:
        movies = await database.search_movie_by_title(query)
        if len(movies) == 1:
            await send_movie_response(message, bot, movies[0], is_admin)
        elif len(movies) > 1:
            text = "🔎 Topilgan natijalar:\n\n"
            for m in movies:
                text += f"🎬 {m[2]} — /kod_{m[1]}\n"
            text += "\nKo'rish uchun /kod_RAQAMI ni bosing."
            await message.answer(text)
        else:
            await message.answer("❌ Bunday nomdagi kino topilmadi.")


# ─── PUL ISHLASH (EARN MONEY) ───────────────────────────────────────────────

@user_router.message(F.text == "💰 Pul ishlash")
async def cmd_earn_money_reply(message: Message):
    await process_earn_money_manual(message)

async def process_earn_money_manual(event: Message | CallbackQuery):
    text = (
        "💰 <b>Pul ishlash bo'limi</b>\n\n"
        "Quyidagi kanallarga obuna bo'lib pul ishlashingiz mumkin:\n"
        "🔹 Telegram kanallar uchun: <b>1 000 so'm</b>\n"
        "🔹 Instagram sahifalar uchun: <b>2 000 so'm</b>\n"
        "🔹 YouTube kanallar uchun: <b>3 000 so'm</b>\n\n"
        "⚠️ <i>Eslatma: Oldin pul olgan kanallaringiz uchun qayta pul berilmaydi.</i>\n\n"
         "Hozirda yangi kanallar mavjud bo'lsa ularga obuna bo'lib hisobingizni to'ldirishingiz mumkin."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏩ Davom ettirish", callback_data="show_earning_list")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_main_menu")]
    ])
    
    if isinstance(event, Message):
        await event.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()

@user_router.callback_query(F.data == "show_earning_list")
async def process_show_earning_list(callback: CallbackQuery):
    db_channels = await database.get_channels()
    all_channels = []
    for db_ch in db_channels:
        if db_ch[4] > 0: # Reward > 0
            icon = "📱"
            if "youtube.com" in db_ch[2] or "youtu.be" in db_ch[2]: icon = "▶️"
            elif "instagram.com" in db_ch[2]: icon = "📸"
            
            all_channels.append({
                "url": db_ch[2],
                "username": db_ch[1],
                "name": db_ch[3],
                "reward": db_ch[4],
                "icon": icon
            })
    
    if not all_channels:
        return await callback.answer("⚠️ Hozircha pul ishlash uchun yangi kanallar yo'q.", show_alert=True)
    
    text = (
        "🔗 <b>Pul ishlash uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
        "Har bir kanal uchun belgilangan mukofotni olishingiz mumkin. "
        "Obuna bo'lgach '✅ Tekshirish' tugmasini bosing."
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_earning_keyboard(all_channels))
    await callback.answer()

@user_router.callback_query(F.data == "earn_money")
async def process_earn_money_callback(callback: CallbackQuery):
    await process_earn_money_manual(callback)


@user_router.message(StateFilter(None))
async def search_handler(message: Message, bot: Bot):
    if not message.text:
        return
    query = message.text.strip()
    if query.startswith("/"):
        if query.startswith("/kod_"):
            pass
        elif message.from_user.id in ADMINS:
            return await message.answer(f"❌ Noma'lum buyruq: {query}")
        else:
            return await message.answer("❌ Noma'lum buyruq. Kino izlash uchun kod yoki nom yuboring.")
    else:
        return await message.answer(
            "⚠️ <b>Kino izlash uchun avval '🎬 Izlash' tugmasini bosing!</b>",
            parse_mode="HTML"
        )
    user = await database.get_user(message.from_user.id)
    is_admin = message.from_user.id in ADMINS
    if not user:
        await database.add_user(message.from_user.id, message.from_user.full_name)
        user = await database.get_user(message.from_user.id)
    l_count = user[5]
    is_prem = user[6]
    if not is_prem and l_count <= 0 and not is_admin:
        return await message.answer("❌ Limitingiz tugadi. Profil bo'limidan limit sotib oling.")
    if query.startswith("/kod_"):
        query = query.replace("/kod_", "")
    if query.isdigit():
        movie = await database.get_movie(query)
        if movie:
            await send_movie_response(message, bot, movie, is_admin)
        else:
            await message.answer("❌ Bunday kodli kino botda mavjud emas.")
    else:
        movies = await database.search_movie_by_title(query)
        if len(movies) == 1:
            await send_movie_response(message, bot, movies[0], is_admin)
        elif len(movies) > 1:
            text = "🔎 Topilgan natijalar:\n\n"
            for m in movies:
                text += f"🎬 {m[2]} — /kod_{m[1]}\n"
            text += "\nKo'rish uchun /kod_RAQAMI ni bosing."
            await message.answer(text)
        else:
            await message.answer("❌ Bunday nomdagi kino topilmadi.")


async def send_movie_response(message: Message, bot: Bot, movie, is_admin: bool):
    await database.update_user_activity(message.from_user.id)
    
    # movie = (id, code, title, type, file_id, duration, coin_cost, created_at)
    coin_cost = movie[6]
    
    if not is_admin:
        user = await database.get_user(message.from_user.id)
        is_premium = user[6]
        limit_count = user[5]
        
        if not is_premium:
            if limit_count < coin_cost:
                return await message.answer(f"❌ Ushbu kinoni ko'rish uchun {coin_cost} ta coin kerak. Sizda esa {limit_count} ta bor.\n\nProfil bo'limidan coin sotib olishingiz mumkin.")
            
            # Limitni kamaytirish
            await database.update_limit(message.from_user.id, limit_count - coin_cost)

    caption = (
        f"🎬 <b>{movie[2]}</b>\n\n"
        f"🔢 Kodi: <code>{movie[1]}</code>\n"
        f"⏱️ Davomiyligi: {movie[5]}\n"
        f"💰 Narxi: {movie[6]} coin\n\n"
        f"🍿 Yoqimli tomosha!"
    )
    
    try:
        await bot.send_video(
            chat_id=message.chat.id,
            video=movie[4],
            caption=caption,
            parse_mode="HTML"
        )
    except Exception:
        # Agar video bo'lmasa document sifatida yuborish
        try:
            await bot.send_document(
                chat_id=message.chat.id,
                document=movie[4],
                caption=caption,
                parse_mode="HTML"
            )
        except Exception as e2:
            await message.answer(f"❌ Faylni yuborishda xatolik: {e2}")

# ─── PUL ISHLASH (EARN MONEY) yakunlandi ─────────────────────────────────────

@user_router.callback_query(F.data == "check_subscription")
async def process_check_all_subs(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    await database.add_user(user_id, callback.from_user.full_name)
    await database.check_and_update_premium(user_id)
    user_data = await database.get_user(user_id)
    is_premium = user_data[6] if user_data else False

    total_reward = 0
    reward_details = []
    already_rewarded_count = 0
    
    db_channels = await database.get_channels()
    # Earning flow channels
    earning_channels = []
    for db_ch in db_channels:
        if db_ch[4] > 0:
            earning_channels.append({
                "url": db_ch[2],
                "username": db_ch[1],
                "name": db_ch[3],
                "reward": db_ch[4]
            })

    for ch in earning_channels:
        is_rewarded = await database.is_channel_rewarded(user_id, ch["url"])
        if is_rewarded:
            already_rewarded_count += 1
            continue

        is_subscribed = False
        chat_identifier = ch.get("username")
        # Telegram check
        if isinstance(chat_identifier, int) or (isinstance(chat_identifier, str) and chat_identifier.startswith("@")):
            try:
                member = await bot.get_chat_member(chat_id=chat_identifier, user_id=user_id)
                if member.status in ["member", "administrator", "creator"]:
                    is_subscribed = True
            except:
                is_subscribed = False
        else:
            # External (IG/YT) - assuming link clicked
            is_subscribed = True 

        if is_subscribed:
            total_reward += ch["reward"]
            reward_details.append(f"✅ {ch['name']} — {ch['reward']} so'm")

    if total_reward > 0:
        msg = (
            f"📊 <b>Tekshiruv natijasi:</b>\n\n"
            f"Siz <b>{len(reward_details)} ta</b> yangi kanalga obuna bo'ldingiz.\n"
            f"Jami mukofot: <b>{total_reward:,} so'm</b>\n\n"
            "Pullarni hisobingizga o'tkazish uchun tugmani bosing:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Hisobga o'tkazish", callback_data=f"transfer_rewards_{total_reward}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="earn_money")]
        ])
        await callback.message.edit_text(msg, parse_mode="HTML", reply_markup=kb)
    else:
        if already_rewarded_count == len(earning_channels) and earning_channels:
            msg = "⚠️ <b>Siz bu kanallarga allaqachon qo'shilgansiz!</b>\n\nMavjud kanallar uchun mukofot puli allaqachon hisobingizga o'tkazilgan."
        else:
            msg = "⚠️ <b>Hali yangi obunalar aniqlanmadi!</b>\n\nIltimos, kanallarga a'zo bo'ling va qaytadan tekshirib ko'ring."
            
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏩ Davom ettirish", callback_data="show_earning_list")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_main_menu")]
        ])
        await callback.message.edit_text(msg, parse_mode="HTML", reply_markup=kb)
    
    # Entry protection (faqat agar yangi rasm jo'natish kerak bo'lsa - lekin bu callback bo'lgani uchun msg o'zgardi)
    # Shuning uchun bu yerda return qilsak ham bo'ladi
    await callback.answer()

@user_router.callback_query(F.data.startswith("transfer_rewards_"))
async def process_transfer_money(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    reward_amount = int(callback.data.split("_")[2])
    
    # Real check before transfer to prevent double-spending or hacks
    # Here we just perform the database update
    # Note: In a production bot, we'd re-verify subscriptions here if needed, 
    # but for simplicity we rely on the previous step's calculation.
    
    # We need to know WHICH channels were rewarded to mark them as done.
    # Re-calculate briefly
    db_channels = await database.get_channels()
    earning_channels = [c for c in db_channels if c[4] > 0]
    
    actual_reward = 0
    rewarded_urls = []
    for ch in earning_channels:
        if not await database.is_channel_rewarded(user_id, ch[2]):
            # Verify sub again
            is_sub = False
            if ch[1] < 0:
                try:
                    m = await bot.get_chat_member(chat_id=ch[1], user_id=user_id)
                    if m.status in ["member", "administrator", "creator"]: is_sub = True
                except: pass
            else: is_sub = True # External
            
            if is_sub:
                actual_reward += ch[4]
                rewarded_urls.append(ch[2])
    
    if actual_reward > 0:
        await database.update_user_balance(user_id, actual_reward)
        for url in rewarded_urls:
            await database.add_channel_reward(user_id, url)
            
        await callback.message.edit_text(
            f"✅ <b>Tabriklaymiz!</b>\n\nHisobingizga <b>{actual_reward:,} so'm</b> o'tkazildi.\n\n"
            f"Joriy balansingizni '👤 Profil' bo'limida ko'rishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="show_main_menu")]
            ])
        )
    else:
        await callback.answer("⚠️ Hali yangi obunalar aniqlanmadi yoki pul allaqachon olingan.", show_alert=True)
    
    await callback.answer()

