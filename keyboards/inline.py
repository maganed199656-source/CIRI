from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def _ext_channel_icon(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "▶️"
    elif "instagram.com" in url:
        return "📸"
    return "🔗"

def get_subscription_keyboard(unsubscribed_tg_channels, external_channels):
    builder = InlineKeyboardBuilder()
    for channel in unsubscribed_tg_channels:
        builder.button(text=f"📱 {channel['name']} — Obuna bo'lish", url=channel["url"])
    for ext in external_channels:
        icon = _ext_channel_icon(ext["url"])
        builder.button(text=f"{icon} {ext['name']} — Obuna bo'lish", url=ext["url"])
    builder.button(text="✅ Tekshirish", callback_data="check_subscription")
    builder.button(text="💰 Pul ishlash", callback_data="earn_money")
    builder.button(text="💎 Premium (kanallarsiz)", callback_data="show_premium")
    builder.adjust(1)
    return builder.as_markup()

def get_earning_keyboard(channels):
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(text=f"{ch['icon']} {ch['name']} — {ch['reward']} so'm", url=ch["url"])
    builder.button(text="⏩ Davom ettirish", callback_data="check_subscription")
    builder.button(text="⬅️ Orqaga", callback_data="show_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎫 Limit sotib olish", callback_data="buy_limit")
    builder.button(text="💎 Premium (Cheksiz)", callback_data="show_premium")
    builder.button(text="💰 Balans to'ldirish", callback_data="top_up_balance")
    builder.button(text="👨‍💻 Adminga murojaat", callback_data="contact_admin")
    builder.button(text="⬅️ Yopish", callback_data="close_menu")
    builder.adjust(1)
    return builder.as_markup()

def premium_plans_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="1 oylik obuna — 15 000 so'm", callback_data="select_prem_1")
    builder.button(text="3 oylik obuna — 35 000 so'm", callback_data="select_prem_3")
    builder.button(text="1 yillik obuna — 65 000 so'm", callback_data="select_prem_12")
    builder.button(text="⬅️ Orqaga", callback_data="show_profile")
    builder.adjust(1)
    return builder.as_markup()

def premium_payment_keyboard(months):
    builder = InlineKeyboardBuilder()
    builder.button(text="🏧 Karta / Bank o'tkazmasi", callback_data=f"method_prem_{months}_manual")
    builder.button(text="💰 Balansdan to'lash", callback_data=f"method_prem_{months}_balance")
    builder.button(text="⬅️ Orqaga", callback_data="show_premium")
    builder.adjust(1)
    return builder.as_markup()

def premium_auto_keyboard(months, pay_url):
    """SafoPay URL tugmasi + chek yuborish tugmasi"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Payme / Click orqali to'lash", url=pay_url)],
        [InlineKeyboardButton(text="📸 Men to'ladim — chekni yuborish", callback_data=f"send_screenshot_{months}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"select_prem_{months}")]
    ])
    return kb

def premium_balance_confirm_keyboard(months):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Balansdan to'lash (tasdiqlash)", callback_data=f"buy_prem_{months}_balance")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"select_prem_{months}")]
    ])
    return kb

def premium_confirm_keyboard(months, method="manual"):
    """Manual (karta) to'lov uchun chek yuborish tugmasi"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📸 To'lov chekini yuborish", callback_data=f"send_screenshot_{months}")
    builder.button(text="⬅️ Orqaga", callback_data=f"select_prem_{months}")
    builder.adjust(1)
    return builder.as_markup()

def limit_payment_keyboard(coin_amount: int):
    """Limit sotib olish — tanlangan coin uchun to'lov usuli"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏧 Karta / Bank o'tkazmasi", callback_data=f"buy_limit_manual_{coin_amount}")],
        [InlineKeyboardButton(text="💰 Balansdan to'lash", callback_data=f"buy_limit_balance_{coin_amount}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_profile")]
    ])
    return kb

def limit_auto_keyboard(pay_url):
    """Limit uchun SafoPay URL tugmasi"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Payme / Click orqali to'lash", url=pay_url)],
        [InlineKeyboardButton(text="📸 Men to'ladim — chekni yuborish", callback_data="send_limit_screenshot")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="buy_limit")]
    ])
    return kb

def admin_approval_keyboard(app_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ruxsat berish", callback_data=f"approve_app_{app_id}")
    builder.button(text="❌ Rad etish", callback_data=f"reject_app_{app_id}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika", callback_data="admin_stats")
    builder.button(text="➕ Kino/Multfilm qo'shish", callback_data="admin_add_movie")
    builder.button(text="➕ Majburiy kanal qo'shish", callback_data="admin_add_channel")
    builder.button(text="🗑 Kino/Multfilm o'chirish", callback_data="admin_del_movie")
    builder.button(text="🗑 Kanal o'chirish", callback_data="admin_del_channel")
    builder.button(text="💰 Balans/Limit berish", callback_data="admin_add_balance")
    builder.button(text="⬅️ Orqaga", callback_data="admin_main")
    builder.adjust(2)
    return builder.as_markup()

def admin_customers_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Foydalanuvchi qidirish", callback_data="admin_search_user")
    builder.button(text="🌟 Premium foydalanuvchilar", callback_data="admin_list_premium")
    builder.button(text="⏳ Muddati tugaganlar", callback_data="admin_list_expired")
    builder.button(text="👥 Barcha foydalanuvchilar", callback_data="admin_list_users_0")
    builder.button(text="⬅️ Orqaga", callback_data="admin_main")
    builder.adjust(1)
    return builder.as_markup()

def admin_user_list_keyboard(users, page, total_pages, list_type):
    builder = InlineKeyboardBuilder()
    for user in users:
        builder.button(text=f"{user[2]} (ID: {user[1]})", callback_data=f"admin_view_user_{user[1]}")
    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_list_{list_type}_{page-1}"))
    if page < total_pages - 1:
        nav_btns.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_list_{list_type}_{page+1}"))
    if nav_btns:
        builder.row(*nav_btns)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_customers"))
    builder.adjust(1)
    return builder.as_markup()

def admin_user_manage_keyboard(user_id, is_premium):
    builder = InlineKeyboardBuilder()
    if not is_premium:
        builder.button(text="💎 +1 oy Premium", callback_data=f"admin_add_prem_{user_id}_1")
        builder.button(text="💎 +3 oy Premium", callback_data=f"admin_add_prem_{user_id}_3")
        builder.button(text="💎 +1 yil Premium", callback_data=f"admin_add_prem_{user_id}_12")
    else:
        builder.button(text="❌ Premium ni o'chirish", callback_data=f"admin_toggle_prem_{user_id}_0")
    
    builder.button(text="🎫 Limit berish", callback_data=f"admin_give_limit_{user_id}")
    builder.button(text="💰 Balansni o'zgartirish", callback_data=f"admin_edit_balance_{user_id}")
    builder.button(text="⬅️ Ro'yxatga qaytish", callback_data="admin_list_users_0")
    builder.adjust(1)
    return builder.as_markup()

def admin_limit_give_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="+5 (5000 so'm)", callback_data=f"admin_set_limit_{user_id}_5")
    builder.button(text="+10 (10000 so'm)", callback_data=f"admin_set_limit_{user_id}_10")
    builder.button(text="+50 (50000 so'm)", callback_data=f"admin_set_limit_{user_id}_50")
    builder.button(text="⬅️ Orqaga", callback_data=f"admin_view_user_{user_id}")
    builder.adjust(1)
    return builder.as_markup()

def admin_balance_manage_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Umumiy tushum", callback_data="admin_total_income")
    builder.button(text="📅 Bugungi tushum", callback_data="admin_daily_income")
    builder.button(text="📜 Sotib olganlar ro'yxati", callback_data="admin_purchased_list")
    builder.button(text="⬅️ Orqaga", callback_data="admin_main")
    builder.adjust(1)
    return builder.as_markup()

def admin_back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="admin_main")
    return builder.as_markup()

def user_back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="show_main_menu")
    return builder.as_markup()

def user_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga qaytish", callback_data="cancel_user_action")
    return builder.as_markup()
