from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def admin_reply_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📊 Statistika"))
    builder.add(KeyboardButton(text="➕ Kino/Multfilm qo'shish"))
    builder.add(KeyboardButton(text="➕ Majburiy kanal qo'shish"))
    builder.add(KeyboardButton(text="🗑 Kino/Multfilm o'chirish"))
    builder.add(KeyboardButton(text="🗑 Kanal o'chirish"))
    builder.add(KeyboardButton(text="📩 Murojaatlar"))
    builder.add(KeyboardButton(text="👥 Mijozlar"))
    builder.add(KeyboardButton(text="💰 Balans boshqaruvi"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def main_reply_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="👤 Profil"))
    builder.add(KeyboardButton(text="🎬 Izlash"))
    builder.add(KeyboardButton(text="💰 Pul ishlash"))
    builder.add(KeyboardButton(text="💰 Balans"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def back_reply_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="⬅️ Orqaga qaytish"))
    return builder.as_markup(resize_keyboard=True)
