from datetime import datetime

def format_lot(lot):
    lot_id, photo_id, year, current_bid, bidder_id, end_time, is_active = lot
    end_dt = datetime.fromisoformat(end_time)
    text = f"📦 *Лот #{lot_id}*\n" \
           f"🚗 Рік: {year}\n" \
           f"💰 Поточна ставка: {current_bid} грн\n" \
           f"⏳ Завершення: {end_dt.strftime('%Y-%m-%d %H:%M')}"
    return text
