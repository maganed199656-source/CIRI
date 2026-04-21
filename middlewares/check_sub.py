from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
import database
from keyboards.inline import get_subscription_keyboard
from config import ADMINS

class CheckSubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        # Obuna bo'lmagan holatda ham Premium/To'lov oqimiga kirishga ruxsat
        if isinstance(event, CallbackQuery):
            callback_data = event.data or ""
            allowed_prefixes = (
                "show_premium",
                "select_prem_",
                "method_prem_",
                "buy_prem_",
                "send_screenshot_",
                "buy_limit",
                "buy_limit_",
                "send_limit_screenshot",
                "top_up_balance",
                "earn_money",
                "check_subscription",
            )
            if callback_data.startswith(allowed_prefixes):
                return await handler(event, data)

        # Adminlar obuna tekshiruvidan ozod
        if user_id in ADMINS:
            return await handler(event, data)

        # /start komandasiga ruxsat (ro'yxatdan o'tish uchun)
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        # Premium foydalanuvchilar obuna tekshiruvidan ozod
        await database.check_and_update_premium(user_id)
        user_data = await database.get_user(user_id)
        if user_data and user_data[6]: # is_premium
            return await handler(event, data)

        bot = data['bot']
        
        # Dinamik kanallar (Database)
        db_channels = await database.get_channels()
        
        # Barcha majburiy kanallar ro'yxati (Initial + DB)
        from handlers.user import INITIAL_CHANNELS
        
        all_tg_channels = []
        all_ext_channels = []
        
        # Initial channels qo'shish
        for ch in INITIAL_CHANNELS:
            if ch["type"] == "telegram":
                all_tg_channels.append({"chat_id": ch["username"], "url": ch["url"], "name": ch["name"]})
            else:
                all_ext_channels.append({"url": ch["url"], "name": ch["name"]})
        
        # DB channels qo'shish
        for ch in db_channels:
            if ch[1] < 0: # TG
                if not any(x["chat_id"] == ch[1] for x in all_tg_channels):
                    all_tg_channels.append({"chat_id": ch[1], "url": ch[2], "name": ch[3]})
            else:
                if not any(x["url"] == ch[2] for x in all_ext_channels):
                    all_ext_channels.append({"url": ch[2], "name": ch[3]})
        
        unsubscribed_tg = []
        for channel in all_tg_channels:
            try:
                member_info = await bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
                if member_info.status not in ["member", "administrator", "creator"]:
                    unsubscribed_tg.append(channel)
            except:
                unsubscribed_tg.append(channel)

        if unsubscribed_tg:
            keyboard = get_subscription_keyboard(unsubscribed_tg, all_ext_channels)
            lines = [
                "❌ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart!</b>",
                "",
                "<b>Holat:</b>"
            ]
            for ch in all_tg_channels:
                is_unsub = any(x["chat_id"] == ch["chat_id"] for x in unsubscribed_tg)
                status = "❌" if is_unsub else "✅"
                lines.append(f"{status} {ch['name']}")
            
            if all_ext_channels:
                lines.append("\n<b>Tashqi havolalar:</b>")
                for ch in all_ext_channels:
                    lines.append(f"🔗 {ch['name']}")
                
            lines.append("\n💎 Premium obuna bilan kanallarsiz foydalanish mumkin.")
            text = "\n".join(lines)
            
            if isinstance(event, CallbackQuery) and event.data == "check_subscription":
                return await handler(event, data)

            if isinstance(event, Message):
                await event.answer(text, parse_mode="HTML", reply_markup=keyboard)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
                await event.answer()
            return

        return await handler(event, data)

    async def _show_welcome(self, event: CallbackQuery):
        try:
            await event.message.delete()
        except:
            pass
            
        welcome_text = (
            "🎬 <b>CINEMA_uz90_bot — Sevimli kinolaringiz markazi!</b>\n\n"
            "Bu bot orqali siz:\n"
            "🔹 Eng so'nggi dunyo premyera kinolarni;\n"
            "🔹 Sevimli va qiziqarli multifilmlarni;\n"
            "🔹 O'zbek tilidagi sifatli filmlarni tomosha qilishingiz mumkin.\n\n"
            "📢 Rasmiy kanal: @CINEMA_uz90\n"
            "👤 Admin: @XONaction\n\n"
            "🚀 <b>Qani boshladik! Botni davom ettirish uchun kanaldagi kino kodini yuboring.</b>"
        )
        await event.message.answer(welcome_text, parse_mode="HTML")
        await event.answer("Muvaffaqiyatli tekshirildi!")
