from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.utils.callback_data import CallbackData
from datetime import datetime, timedelta
import asyncio

from database import Database
from keyboard import choose_lang_button, generate_contact_button, generate_reserve_button, generate_category_menu, \
    generate_period_buttons, generate_calculator_people, generate_alternative_times, generate_all_reserving, \
    generate_booking_cancel, generate_settings
from langs import langs


bot = Bot(token='')
dp = Dispatcher(bot)
db = Database()


@dp.message_handler(commands=['start'])
async def command_start(message: Message):
    chat_id = message.chat.id
    db.create_users_table()
    await bot.send_message(chat_id, 'Select language\nВыберите язык\nTilni tanlang', reply_markup=choose_lang_button())


@dp.message_handler(regexp=r'(\🇺🇸 English|\🇷🇺 Русский|\🇺🇿 Ozbek)')
async def get_lang_register_user(message: Message):
    lang = message.text
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    user = db.get_user_by_chat_id(chat_id)
    if lang == '🇷🇺 Русский':
        lang = 'ru'
    elif lang == '🇺🇿 Ozbek':
        lang = 'uz'
    else:
        lang = 'en'
    if user:
        db.set_user_language(chat_id, lang)
    else:
        db.first_register_user(chat_id, full_name)
        db.set_user_language(chat_id, lang)
        await message.answer(langs[lang]['select_language'])
    await message.answer(langs[lang]['registration'], reply_markup=generate_contact_button(lang))


@dp.message_handler(content_types=['contact'])
async def finish_register(message: Message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    lang = db.get_user_language(chat_id)
    db.update_user_to_finish_register(chat_id, phone)
    await message.answer(langs[lang]['reg_complete'], reply_markup=ReplyKeyboardRemove())


@dp.message_handler(commands=['help'])
async def command_help(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await bot.send_message(chat_id, langs[lang]['help'])


@dp.message_handler(commands=['booking'])
async def command_booking(message: Message):
    chat_id = message.chat.id
    db.create_booking_table()
    lang = db.get_user_language(chat_id)
    await bot.send_message(chat_id, langs[lang]['booking'], reply_markup=generate_reserve_button(lang))


@dp.message_handler(regexp='Booking|Забронировать|Buyurtma qilish')
async def make_booking(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    db.insert_categories()
    await message.answer(langs[lang]['category'], reply_markup=generate_category_menu(lang))


@dp.callback_query_handler(lambda call: call.data.startswith('category_'))
async def ask_period(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    category = call.data.split('_')[1]
    await bot.edit_message_text(
        langs[lang]['period'],
        chat_id,
        call.message.message_id,
        reply_markup=generate_period_buttons(lang=lang, category=category)
    )


@dp.callback_query_handler(lambda call: 'main_menu' in call.data)
async def return_to_main_menu(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=langs[lang]['category'], reply_markup=generate_category_menu(lang))


calendar_callback = CallbackData('calendar', 'action', 'year', 'month', 'day', 'category')


@dp.callback_query_handler(calendar_callback.filter(action=['day']))
async def select_date(call: CallbackQuery, callback_data: dict):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    year = int(callback_data['year'])
    month = int(callback_data['month'])
    day = int(callback_data['day'])
    category_id = callback_data['category']

    date = datetime(year, month, day).date()
    db.get_date(category_id, date, chat_id)

    lang = db.get_user_language(chat_id)
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=f"{langs[lang]['date_selected']} {date.strftime('%Y-%m-%d')}")
    await bot.send_message(chat_id, langs[lang]['time'])
    await call.answer()


@dp.callback_query_handler(calendar_callback.filter(action=['prev_month', 'next_month']))
async def change_month(call: CallbackQuery, callback_data: dict):
    year = int(callback_data['year'])
    month = int(callback_data['month'])
    category = callback_data['category']
    lang = db.get_user_language(call.message.chat.id)

    await bot.edit_message_text(
        langs[lang]['period'],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=generate_period_buttons(lang=lang, year=year, month=month, category=category)
    )
    await call.answer()


@dp.message_handler(regexp='^(?:[01]\d|2[0-3]):[0-5]\d$')
async def get_time_ask_people(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    time = message.text
    db.update_time(time, chat_id)
    await message.answer(langs[lang]['people'], reply_markup=generate_calculator_people(lang))


@dp.callback_query_handler(lambda call: 'back' in call.data)
async def return_to_time(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    await bot.delete_message(chat_id, message_id)
    await bot.send_message(chat_id, langs[lang]['time'])


@dp.callback_query_handler(lambda call: 'plus' in call.data)
async def increase_people(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    _, quantity = call.data.split('_')
    quantity = int(quantity)
    quantity += 1
    message_id = call.message.message_id
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=langs[lang]['people'],
                                reply_markup=generate_calculator_people(lang=lang, c=quantity))


@dp.callback_query_handler(lambda call: 'minus' in call.data)
async def decrease_people(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    _, quantity = call.data.split('_')
    quantity = int(quantity)
    message_id = call.message.message_id
    if quantity <= 1:
        await bot.answer_callback_query(call.id, langs[lang]['zero'])
        pass
    else:
        quantity -= 1
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=langs[lang]['people'],
                                    reply_markup=generate_calculator_people(lang=lang, c=quantity))


@dp.callback_query_handler(lambda call: 'reserve' in call.data)
async def check_availability(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    _, quantity = call.data.split('_')
    quantity = int(quantity)
    last_booking = db.get_last_booking(chat_id)
    if not last_booking:
        await bot.send_message(chat_id, langs[lang]['booking_error'])
        await call.answer()
        return

    category_id = last_booking['category_id']
    date = last_booking['date']
    time = last_booking['time']

    if db.check_availability(category_id, date, time):
        db.update_amount_people(chat_id, quantity)
        await bot.send_message(chat_id, langs[lang]['booking_successful'])
    else:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=langs[lang]['booking_unavailable'])
        await bot.send_message(chat_id, langs[lang]['choose_alternative'],
                               reply_markup=generate_alternative_times(date, category_id, lang))
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('alternative_'))
async def select_alternative_time(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    alternative_time = call.data.split('_')[1]
    db.update_time(alternative_time, chat_id)
    await bot.send_message(chat_id, langs[lang]['booking_successful'])
    await call.answer()


@dp.message_handler(commands=['cancel'])
async def command_cancel(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await bot.send_message(chat_id, langs[lang]['choose_booking'], reply_markup=generate_all_reserving(chat_id))


@dp.callback_query_handler(lambda call: call.data.startswith('view-booking_'))
async def view_booking(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    booking_id = int(call.data.split('_')[1])
    booking = db.get_booking_by_id(booking_id)
    if booking:
        text = (f"{langs[lang]['booking_name']}: {booking['category_name']}\n"
                f"{langs[lang]['booking_date']}: {booking['date']}\n"
                f"{langs[lang]['booking_time']}: {booking['time']}\n"
                f"{langs[lang]['booking_people']}: {booking['amount_people']}")
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text,
                                    reply_markup=generate_booking_cancel(lang, booking_id))
    else:
        await bot.send_message(chat_id, langs[lang]['booking_not_found'])


@dp.callback_query_handler(lambda call: call.data.startswith('cancel_'))
async def cancel_booking(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    booking_id = int(call.data.split('_')[1])
    db.delete_booking(booking_id)
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=langs[lang]['booking_cancelled'])
    await bot.send_message(chat_id, langs[lang]['choose_booking'], reply_markup=generate_all_reserving(chat_id))


@dp.callback_query_handler(lambda call: call.data.startswith('exit'))
async def back_to_bookings(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = db.get_user_language(chat_id)
    message_id = call.message.message_id
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=langs[lang]['choose_booking'],
                                reply_markup=generate_all_reserving(chat_id))


@dp.message_handler(regexp='Settings|Настройки|Sozlamalar')
async def settings(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await message.answer(langs[lang]['choose_option'], reply_markup=generate_settings(lang))


@dp.message_handler(regexp='Change language|Сменить язык|Tilni ozgartiring')
async def change_language(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await message.answer(langs[lang]['select_lang'], reply_markup=choose_lang_button())


@dp.message_handler(regexp='⬅ Back|⬅ Назад|⬅ Orqaga')
async def change_language(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await message.answer(langs[lang]['choose_option'], reply_markup=generate_reserve_button(lang))


async def send_reminders():
    while True:
        now = datetime.now()
        reminder_time = now + timedelta(hours=24)
        bookings = db.get_bookings_for_reminder(reminder_time)

        for booking in bookings:
            chat_id = booking[1]
            lang = db.get_user_language(chat_id)
            await bot.send_message(chat_id, f"{langs[lang]['reminder']}: {booking[5]} - {booking[3]} {booking[4]}")
            db.mark_reminder_sent(booking[0])
        await asyncio.sleep(3600)


async def on_startup(dp):
    db.create_booking_table()
    asyncio.create_task(send_reminders())

executor.start_polling(dp, on_startup=on_startup)
