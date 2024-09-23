from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
import calendar

from langs import langs
from database import *

db = Database()


def choose_lang_button():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    english = KeyboardButton(text='🇺🇸 English')
    russian = KeyboardButton(text='🇷🇺 Русский')
    uzbek = KeyboardButton(text='🇺🇿 Ozbek')
    markup.row(english, russian, uzbek)
    return markup


def generate_contact_button(lang):
    return ReplyKeyboardMarkup([
        [KeyboardButton(text=langs[lang]['contact'], request_contact=True)]
    ], resize_keyboard=True)


def generate_reserve_button(lang):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    reserve = KeyboardButton(langs[lang]['reserve'])
    settings = KeyboardButton(langs[lang]['settings'])
    markup.row(reserve, settings)
    return markup


def generate_category_menu(lang):
    markup = InlineKeyboardMarkup(row_width=1)
    categories = db.get_all_categories()
    buttons = []
    for category in categories:
        if lang == 'en':
            btn = InlineKeyboardButton(text=category[1], callback_data=f'category_{category[0]}')
            buttons.append(btn)
        elif lang == 'ru':
            btn = InlineKeyboardButton(text=category[2], callback_data=f'category_{category[0]}')
            buttons.append(btn)
        else:
            btn = InlineKeyboardButton(text=category[3], callback_data=f'category_{category[0]}')
            buttons.append(btn)
    markup.add(*buttons)
    return markup


calendar_callback = CallbackData('calendar', 'action', 'year', 'month', 'day', 'category')


def generate_period_buttons(lang, year=None, month=None, category=None):
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    markup = InlineKeyboardMarkup(row_width=7)

    month_name = calendar.month_name[month]
    markup.add(InlineKeyboardButton(f'{month_name} {year}', callback_data='ignore'))

    week_days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    markup.add(*[InlineKeyboardButton(day, callback_data='ignore') for day in week_days])

    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(' ', callback_data='ignore'))
            else:
                row.append(InlineKeyboardButton(
                    str(day),
                    callback_data=calendar_callback.new('day', year, month, day, category)
                ))
        markup.row(*row)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1

    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    markup.add(
        InlineKeyboardButton('Prev',
                             callback_data=calendar_callback.new('prev_month', prev_year, prev_month, 0, category)),
        InlineKeyboardButton('Next',
                             callback_data=calendar_callback.new('next_month', next_year, next_month, 0, category))
    )
    markup.row(
        InlineKeyboardButton(text=langs[lang]['back'], callback_data='main_menu')
    )
    return markup


def generate_calculator_people(lang, c=1):
    markup = InlineKeyboardMarkup(row_width=3)
    quantity = c

    buttons = []
    btn_minus = InlineKeyboardButton(text=str('➖'), callback_data=f'minus_{quantity}')
    btn_quantity = InlineKeyboardButton(text=str(quantity), callback_data=f'coll')
    btn_plus = InlineKeyboardButton(text=str('➕'), callback_data=f'plus_{quantity}')
    buttons.append(btn_minus)
    buttons.append(btn_quantity)
    buttons.append(btn_plus)
    markup.add(*buttons)
    markup.row(
        InlineKeyboardButton(text=langs[lang]['book'], callback_data=f'reserve_{quantity}')
    )
    markup.row(
        InlineKeyboardButton(text=langs[lang]['back'], callback_data=f'back')
    )
    return markup


def generate_alternative_times(date, category_id, lang):
    markup = InlineKeyboardMarkup(row_width=3)
    available_times = db.get_available_times(date, category_id)

    for time in available_times:
        btn = InlineKeyboardButton(text=time, callback_data=f'alternative_{time}')
        markup.add(btn)

    markup.row(
        InlineKeyboardButton(text=langs[lang]['back'], callback_data='back')
    )
    return markup


def generate_all_reserving(chat_id):
    markup = InlineKeyboardMarkup(row_width=3)
    bookings = db.get_all_booking(chat_id)

    for book in bookings:
        btn_text = f"{book[2]} {book[3]}"
        btn = InlineKeyboardButton(text=btn_text, callback_data=f'view-booking_{book[0]}')
        markup.add(btn)
    return markup


def generate_booking_cancel(lang, booking_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(
        InlineKeyboardButton(text=langs[lang]['cancel'], callback_data=f'cancel_{booking_id}')
    )
    markup.row(
        InlineKeyboardButton(text=langs[lang]['back'], callback_data=f'exit')
    )
    return markup


def generate_settings(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=langs[lang]['change_lang']), KeyboardButton(text=langs[lang]['back'])],
        ],
        resize_keyboard=True
    )
