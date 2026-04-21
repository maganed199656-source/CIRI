import asyncio
import logging
import sys
import os
from collections import deque
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher
from aiohttp import web

from config import BOT_TOKEN
from database import init_db
from handlers.user import user_router
from handlers.admin import admin_router
from middlewares.check_sub import CheckSubscriptionMiddleware

LOG_BUFFER: deque[str] = deque(maxlen=500)
START_TIME = datetime.now(timezone.utc)


class BufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            LOG_BUFFER.append(self.format(record))
        except Exception:
            pass


async def status_handler(request: web.Request) -> web.Response:
    uptime = datetime.now(timezone.utc) - START_TIME
    html = (
        "<!doctype html><meta charset=utf-8>"
        "<title>CINEMA_uz90 bot — status</title>"
        "<style>body{font-family:system-ui,sans-serif;background:#0b0b10;color:#e8e8ee;"
        "max-width:920px;margin:24px auto;padding:0 16px}"
        "h1{color:#7ee787} .ok{color:#7ee787} pre{background:#15151c;padding:12px;"
        "border-radius:8px;overflow:auto;max-height:70vh;font-size:12px;line-height:1.4}"
        ".meta{color:#9aa}</style>"
        f"<h1>● Bot ishlayapti</h1>"
        f"<p class=meta>Boshlangan: {START_TIME.isoformat()}<br>"
        f"Uptime: {str(uptime).split('.')[0]}</p>"
        "<h3>Oxirgi loglar</h3>"
        "<pre>" + "\n".join(LOG_BUFFER) + "</pre>"
    )
    return web.Response(text=html, content_type="text/html")


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "uptime_seconds": int((datetime.now(timezone.utc) - START_TIME).total_seconds()),
        "logs_kept": len(LOG_BUFFER),
    })


async def start_status_server(port: int) -> None:
    app = web.Application()
    app.router.add_get("/", status_handler)
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.getLogger(__name__).info(f"Status server: http://0.0.0.0:{port}")


async def main() -> None:
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(admin_router)
    dp.include_router(user_router)

    port = int(os.getenv("PORT", "8080"))
    await start_status_server(port)

    try:
        await dp.start_polling(bot)
    finally:
        from database import close_db
        await close_db()


if __name__ == "__main__":
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    buf = BufferHandler()
    buf.setFormatter(logging.Formatter(fmt))
    handlers.append(buf)
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")
