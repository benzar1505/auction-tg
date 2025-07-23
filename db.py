import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('auction.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        photo_id TEXT,
        year TEXT,
        current_bid INTEGER,
        highest_bidder_id INTEGER,
        end_time TEXT,
        is_active INTEGER
    )
''')
conn.commit()

def create_lot(photo_id, year, start_bid, duration_minutes):
    end_time = (datetime.now() + timedelta(minutes=duration_minutes)).isoformat()
    cursor.execute('''
        INSERT INTO lots (photo_id, year, current_bid, highest_bidder_id, end_time, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (photo_id, year, start_bid, None, end_time))
    conn.commit()
    return cursor.lastrowid

def get_active_lots():
    cursor.execute('SELECT * FROM lots WHERE is_active = 1')
    return cursor.fetchall()

def update_bid(lot_id, user_id, bid_amount):
    cursor.execute('''
        UPDATE lots SET current_bid = ?, highest_bidder_id = ? WHERE id = ?
    ''', (bid_amount, user_id, lot_id))
    conn.commit()

def get_lot_by_id(lot_id):
    cursor.execute('SELECT * FROM lots WHERE id = ?', (lot_id,))
    return cursor.fetchone()

def close_lot(lot_id):
    cursor.execute('UPDATE lots SET is_active = 0 WHERE id = ?', (lot_id,))
    conn.commit()
