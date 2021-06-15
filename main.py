import requests
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, update
from aiogram.utils import executor

from config import TOKEN
from models import DBManager

from parse_yandex_url import get_yandex_reviews

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
db = DBManager()


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Категории🥙", "Случайный🎲", "Помощь🏳️",]
    name = message.from_user.first_name
    keyboard.add(*buttons)
    await message.answer(f'Привет {name}!\nЯ помогу тебе найти ресторан на сегодня\nЧтобы начать, нажми на одну из кнопок', reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Помощь🏳️")
async def process_help_command(message: types.Message):
    await message.reply(
        "Чтобы сделать выбор из категорий,\n"
        "нажмите на кнопку: Категории.\n" \
        "Чтобы выбрать случайный ресторан\n"
        "нажмите на кнопку: Случайный.\n" \
        )


@dp.message_handler(lambda msg: msg.text == "Категории🥙")
async def get_categories_command(msg: types.Message):
    """Получение всех категорий"""
    categories = db.get_categories()
    keyboard = types.InlineKeyboardMarkup()

    for category in categories:
        keyboard.add(
            InlineKeyboardButton(
                text=category,
                callback_data=f'ctg_{category}')

        )

    await bot.send_message(msg.from_user.id, 'Выберите одну категорию:', reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text == "Случайный🎲")
async def get_product_random(msg: types.Message):
    """Вывод рандомного ресторана"""
    randoms = db.get_product_random()
    keyboard = types.InlineKeyboardMarkup()
    for random in randoms:
        keyboard.add(
            InlineKeyboardButton(
                text=random,
                callback_data=f'rand_{random}'
            )
        )

    await bot.send_message(msg.from_user.id, 'Случайный ресторан:', reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data and call.data.startswith('ctg_'))
async def get_products_callback(callback_query: types.CallbackQuery):
    """Выбирает все рестики из определенной категории"""
    query = callback_query.data.replace('ctg_', '')  # Убрать пометку callback'ов
    products = db.get_from_category(query)
    keyboard = types.InlineKeyboardMarkup()
    for product in products:
        keyboard.add(
            InlineKeyboardButton(
                text=product,
                callback_data=f'prdct_{product}'
            )
        )
    await callback_query.answer()
    await bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=f'{query}:',
        reply_markup=keyboard
    )


@dp.callback_query_handler(lambda call: call.data and call.data.startswith('prdct_'))
async def get_products_callback(callback_query: types.CallbackQuery):
    """Выбирает рестик из категории"""
    query = callback_query.data.replace('prdct_', '')  # Убрать пометку callback'ов
    product = db.get_product(query)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text='Сайт',
            url=product[6]
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text='Открыть на карте',
            url=product[8]
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text='Показать отзывы',
            callback_data=f'revw_{product[8]}'
        )
    )

    answer = f'*Ресторан:*{product[1]}\n*Описание:*{product[2]}\n*Адрес:*\n{product[5]}\n*Телефон:*{product[7]}'
    await callback_query.answer()
    await bot.send_photo(
        chat_id=callback_query.from_user.id,
        caption=answer,
        reply_markup=keyboard,
        photo=product[3],
        parse_mode='markdown')


@dp.callback_query_handler(lambda call: call.data and call.data.startswith('rand_'))
async def get_products_callback(callback_query: types.CallbackQuery):
    """Вывод случайного ресторана"""
    query = callback_query.data.replace('rand_', '')  # Убрать пометку callback'ов
    product = db.get_product(query)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text='Сайт',
            url=product[6]
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text='Открыть на карте',
            url=product[8]
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text='Показать отзывы',
            callback_data=f'revw_{product[8]}'
        )
    )

    answer = f'*Ресторан:*{product[1]}\n*Описание:*{product[2]}\n*Адрес:*\n{product[5]}\n*Телефон:*{product[7]}'
    await callback_query.answer()
    await bot.send_photo(
        chat_id=callback_query.from_user.id,
        caption=answer,
        reply_markup=keyboard,
        photo=product[3],
        parse_mode='markdown')


star_unocode = '\U00002b50'


@dp.callback_query_handler(lambda call: call.data and call.data.startswith('revw_'))
async def get_products_callback(callback_query: types.CallbackQuery):
    """Вывод отзывов"""
    query = callback_query.data.replace('revw_', '')  # Убрать пометку callback'ов

    reviews = get_yandex_reviews(query)
    reviews_str = ''
    for review in reviews:
        idx = review['index'] + 1
        name = review['reviewer_name']
        review_rate = review['review_rate']
        review_text = review['review_text']

        rate_str = f'{star_unocode}' * review_rate
        review_str = f'*{idx}. {name}* {rate_str}\n{review_text}\n\n'

        reviews_str += review_str

    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, reviews_str, parse_mode='markdown')


if __name__ == '__main__':
    executor.start_polling(dp)
