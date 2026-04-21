import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8487130667:AAEEmhKAORptry7bNppZb4Enxgg7k8NfTwY")
BOT_NAME = "KinoloveUzBot"
ADMINS = [int(x) for x in os.getenv("ADMINS", "5714788187").split(",")]
MOVIE_CHANNEL = int(os.getenv("MOVIE_CHANNEL", "-1003924104096"))

LIMIT = 10
PREMIUM_PRICE_1 = 15000
PREMIUM_PRICE_3 = 35000
PREMIUM_PRICE_12 = 65000
MOVIE_COST = 2
LIMIT_PRICE = 5000

# =====================================================================
# SafoPay to'lov linklari
# Har bir summa uchun SafoPay dashboard'dan alohida link yarating:
# https://safopay.uz → Merchant panel → To'lov sahifasi yaratish
# =====================================================================
PAYMENT_LINKS = {
    15000: "https://safopay.uz/pay/fb3cd0d1d408cd8a9913420e5b97dc2d9d259a4f9ffb829a95887f544115ded5",
    35000: "https://safopay.uz/pay/fb3cd0d1d408cd8a9913420e5b97dc2d9d259a4f9ffb829a95887f544115ded5",
    65000: "https://safopay.uz/pay/fb3cd0d1d408cd8a9913420e5b97dc2d9d259a4f9ffb829a95887f544115ded5",
    5000:  "https://safopay.uz/pay/fb3cd0d1d408cd8a9913420e5b97dc2d9d259a4f9ffb829a95887f544115ded5",
}

ADMIN_USER = "@XONaction"
ADMIN_CARD = "4916990323171766"
ADMIN_CARD_NAME = "Matnazarov Shoxruhxon"

LOGO_PATH = os.getenv("LOGO_PATH", "assets/logo.png")

TELEGRAM_CHANNELS = []
EXTERNAL_CHANNELS = []
