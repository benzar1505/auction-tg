import telebot
import os

# Отримуємо токен з секретів Replit
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Обробка команди /start
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привіт! Це аукціон-бот 🚗")

# Обробка звичайного тексту
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ти написав: {message.text}")

# Запуск бота
bot.polling(non_stop=True)
