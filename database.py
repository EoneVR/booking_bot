import sqlite3
from datetime import datetime, timedelta


class Database:
    def __init__(self):
        self.database = sqlite3.connect('reserve.db', check_same_thread=False)
        self.create_users_table()
        self.create_categories_table()

    def manager(self, sql, *args,
                fetchone: bool = False,
                fetchall: bool = False,
                commit: bool = False):
        with self.database as db:
            cursor = db.cursor()
            cursor.execute(sql, args)
            if commit:
                result = db.commit()
            if fetchone:
                result = cursor.fetchone()
            if fetchall:
                result = cursor.fetchall()
            return result

    def create_users_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE,
            full_name TEXT,
            phone TEXT,
            language TEXT
            )
            '''
        self.manager(sql, commit=True)

    def get_user_by_chat_id(self, chat_id):
        sql = '''
        SELECT * FROM users WHERE chat_id = ?
        '''
        return self.manager(sql, chat_id, fetchone=True)

    def first_register_user(self, chat_id, full_name):
        sql = '''
        INSERT INTO users(chat_id, full_name) VALUES (?,?)
        '''
        self.manager(sql, chat_id, full_name, commit=True)

    def update_user_to_finish_register(self, chat_id, phone):
        sql = '''
        UPDATE users SET phone = ?
        WHERE chat_id = ?
        '''
        self.manager(sql, phone, chat_id, commit=True)

    def set_user_language(self, chat_id, lang):
        user = self.get_user_by_chat_id(chat_id)
        if user:
            sql = '''
            UPDATE users SET language = ? WHERE chat_id = ?
            '''
            self.manager(sql, lang, chat_id, commit=True)
        else:
            sql = '''
            INSERT INTO users (chat_id, language) VALUES (?,?)
            '''
            self.manager(sql, chat_id, lang, commit=True)

    def get_user_language(self, chat_id):
        sql = '''
        SELECT language FROM users WHERE chat_id = ?
        '''
        result = self.manager(sql, chat_id, fetchone=True)
        if result:
            return result[0]
        return None

    def create_categories_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS categories(
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name VARCHAR(100),
        category_name_ru VARCHAR(100) NOT NULL,
        category_name_uz VARCHAR(100) NOT NULL
        )
        '''
        self.manager(sql, commit=True)

    def categories_table_empty(self):
        sql = '''
        SELECT COUNT(*) FROM categories
        '''
        result = self.manager(sql, fetchone=True)
        return result[0] == 0

    def insert_categories(self):
        if self.categories_table_empty():
            sql = '''
            INSERT INTO categories (category_name, category_name_ru, category_name_uz) VALUES
            ('Air tickets', 'Авиабилеты', 'Aviabiletlar'),
            ('Hotels', 'Отели и гостиницы', 'Mehmonxonalar'),
            ('Restaurants', 'Столик в рестаране', 'Restoranlar'),
            ('Museums', 'Музеи', 'Muzeylar'),
            ('Special-events', 'Special-events', 'Special-events')
            '''
            self.manager(sql, commit=True)

    def get_all_categories(self):
        sql = '''
        SELECT * FROM categories
        '''
        return self.manager(sql, fetchall=True)

    def create_booking_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS booking(
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER REFERENCES categories(category_id),
        date DATE,
        time TEXT,
        amount_people INTEGER,
        chat_id INTEGER REFERENCES users(chat_id),
        reminder_sent BOOLEAN DEFAULT 0
        )
        '''
        self.manager(sql, commit=True)

    def get_date(self, category_id, date, chat_id):
        sql = '''
        INSERT INTO booking(category_id, date, chat_id) VALUES (?,?,?)
        '''
        self.manager(sql, category_id, date, chat_id, commit=True)

    def update_time(self, time, chat_id):
        sql = '''
        UPDATE booking
        SET time = ?
        WHERE chat_id = ? AND time IS NULL
        '''
        self.manager(sql, time, chat_id, commit=True)

    def update_amount_people(self, chat_id, amount_people):
        sql = '''
        UPDATE booking
        SET amount_people = ?
        WHERE chat_id = ? AND amount_people IS NULL
        '''
        self.manager(sql, amount_people, chat_id, commit=True)

    def generate_time_slots(self, start_time="09:00", end_time="21:00", interval_minutes=60):
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        slots = []
        while start <= end:
            slots.append(start.strftime("%H:%M"))
            start += timedelta(minutes=interval_minutes)
        return slots

    def get_available_times(self, date, category_id):
        sql = '''
        SELECT time FROM booking
        WHERE date = ? AND category_id = ?
        '''
        booked_times = self.manager(sql, date, category_id, fetchall=True)
        booked_times = [time[0] for time in booked_times]

        all_possible_times = self.generate_time_slots()

        available_times = [time for time in all_possible_times if time not in booked_times]
        return available_times

    def get_max_capacity(self, category_id):
        if category_id == 1:
            return 5
        elif category_id == 2:
            return 10
        elif category_id == 3:
            return 20
        elif category_id == 4:
            return 10
        else:
            return 5

    def check_availability(self, category_id, date, time):
        max_capacity = self.get_max_capacity(category_id)
        sql = '''
        SELECT COUNT(*)
        FROM booking
        WHERE category_id = ? AND date = ? AND time = ?
        '''
        result = self.manager(sql, category_id, date, time, fetchone=True)
        return result[0] < max_capacity

    def get_last_booking(self, chat_id):
        sql = '''
        SELECT category_id, date, time
        FROM booking
        WHERE chat_id = ?
        ORDER BY booking_id DESC
        LIMIT 1
        '''
        result = self.manager(sql, chat_id, fetchone=True)
        if result:
            return {
                'category_id': result[0],
                'date': result[1],
                'time': result[2]
            }
        return None

    def get_all_booking(self, chat_id):
        sql = '''
        SELECT * FROM booking
        WHERE chat_id = ?
        '''
        return self.manager(sql, chat_id, fetchall=True)

    def get_booking_by_id(self, booking_id):
        sql = '''
        SELECT b.booking_id, b.date, b.time, b.amount_people, c.category_name
        FROM booking b
        JOIN categories c ON b.category_id = c.category_id
        WHERE b.booking_id = ?
        '''
        result = self.manager(sql, booking_id, fetchone=True)
        if result:
            return {
                'booking_id': result[0],
                'date': result[1],
                'time': result[2],
                'amount_people': result[3],
                'category_name': result[4]
            }
        return None

    def delete_booking(self, booking_id):
        sql = '''
        DELETE FROM booking
        WHERE booking_id = ?
        '''
        self.manager(sql, booking_id, commit=True)

    def get_bookings_for_reminder(self, reminder_time):
        sql = '''
        SELECT b.booking_id, b.chat_id, b.category_id, b.date, b.time, c.category_name
        FROM booking b
        JOIN categories c ON b.category_id = c.category_id
        WHERE b.reminder_sent = 0 
        AND datetime(b.date || ' ' || b.time) BETWEEN ? AND ?
        '''
        reminder_start = reminder_time.strftime("%Y-%m-%d %H:%M:%S")
        reminder_end = (reminder_time + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        return self.manager(sql, reminder_start, reminder_end, fetchall=True)

    def mark_reminder_sent(self, booking_id):
        sql = '''
        UPDATE booking
        SET reminder_sent = 1
        WHERE booking_id = ?
        '''
        self.manager(sql, booking_id, commit=True)
