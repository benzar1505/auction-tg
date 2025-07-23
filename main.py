from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import logging
import asyncio

from config import API_TOKEN, ADMINS
import db
import utils

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode='Markdown')
dp = Dispatcher(bot)

# Список активних лотів у памʼяті (для оновлення часу)
active_auctions = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("👋 Привіт! Це бот аукціону.\nКоманда для адмінів: /newlot")

@dp.message_handler(commands=['newlot'])
async def new_lot(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔ У вас немає прав для створення лота.")
    
    await message.answer("🖼 Надішліть фото лота.")
    await NewLot.waiting_for_photo.set()

# FSM (Finite State Machine) для заповнення форми
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

dp.storage = MemoryStorage()

class NewLot(StatesGroup):
    waiting_for_photo = State()
    waiting_for_year = State()
    waiting_for_start_bid = State()
    waiting_for_duration = State()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=NewLot.waiting_for_photo)
async def lot_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await message.answer("✏️ Введіть рік:")
    await NewLot.waiting_for_year.set()

@dp.message_handler(state=NewLot.waiting_for_year)
async def lot_year(message: types.Message, state: FSMContext):
    await state.update_data(year=message.text)
    await message.answer("💵 Введіть стартову ставку:")
    await NewLot.waiting_for_start_bid.set()

@dp.message_handler(state=NewLot.waiting_for_start_bid)
async def lot_start_bid(message: types.Message, state: FSMContext):
    await state.update_data(start_bid=int(message.text))
    await message.answer("⏱ Введіть тривалість аукціону (в хвилинах):")
    await NewLot.waiting_for_duration.set()

@dp.message_handler(state=NewLot.waiting_for_duration)
async def lot_duration(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lot_id = db.create_lot(
        photo_id=data['photo_id'],
        year=data['year'],
        start_bid=data['start_bid'],
        duration_minutes=int(message.text)
    )
    lot = db.get_lot_by_id(lot_id)
    text = utils.format_lot(lot)
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔼 Зробити ставку", callback_data=f"bid_{lot_id}")
    )
    await bot.send_photo(chat_id=message.chat.id, photo=data['photo_id'], caption=text, reply_markup=keyboard)
    await state.finish()

    # Запускаємо таймер завершення
    asyncio.create_task(lot_timer(lot_id))

@dp.callback_query_handler(lambda c: c.data.startswith('bid_'))
async def handle_bid(call: types.CallbackQuery):
    lot_id = int(call.data.split('_')[1])
    lot = db.get_lot_by_id(lot_id)
    if not lot or not lot[6]:
        return await call.answer("⛔ Аукціон завершено.")

    await call.message.answer("💰 Введіть вашу ставку (числом):")

    @dp.message_handler()
    async def receive_bid(message: types.Message):
        bid = int(message.text)
        current = lot[3]
        if bid <= current:
            return await message.answer("⚠️ Ставка має бути вищою за поточну.")
        db.update_bid(lot_id, message.from_user.id, bid)
        await message.answer("✅ Ваша ставка прийнята!")
        await call.message.edit_caption(utils.format_lot(db.get_lot_by_id(lot_id)), reply_markup=call.message.reply_markup)
        dp.message_handlers.unregister(receive_bid)

async def lot_timer(lot_id):
    lot = db.get_lot_by_id(lot_id)
    end_time = datetime.fromisoformat(lot[5])
    now = datetime.now()
    delay = (end_time - now).total_seconds()
    await asyncio.sleep(delay)
    db.close_lot(lot_id)
    lot = db.get_lot_by_id(lot_id)
    if lot[4]:
        winner_mention = f"[user](tg://user?id={lot[4]})"
        text = f"🏁 Аукціон завершено!\nПереможець: {winner_mention}\nСтавка: {lot[3]} грн"
    else:
        text = "❌ Аукціон завершено без переможця."
    await bot.send_message(chat_id=ADMINS[0], text=text)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
