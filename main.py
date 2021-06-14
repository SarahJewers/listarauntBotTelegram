from random import randint

import requests
import updater
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
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
    buttons = ["Кушать", "Случайный", "Локация", "Помощь"]
    keyboard.add(*buttons)
    await message.answer(
        "Привет!\n" \
        "Я помогу тебе найти ресторан на сегодня.\n" \
        "Чтобы начать напиши: Кушать", \
        reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Помощь")
async def process_help_command(message: types.Message):
    await message.reply(
        "Помогите\n" \
        "пожалуйста помогите.\n" \
        "Чтобы начать напиши: Кушать" \
        )


@dp.message_handler(lambda msg: msg.text == "Кушать")
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

    await bot.send_message(msg.from_user.id, 'Категории:', reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text == "Случайный")
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

    await bot.send_message(msg.from_user.id, 'Вотоно:', reply_markup=keyboard)


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
    await bot.send_photo(
        chat_id=callback_query.from_user.id,
        caption=answer,
        reply_markup=keyboard,
        photo=product[3],
        parse_mode='markdown')


@dp.callback_query_handler(lambda call: call.data and call.data.startswith('rand_'))
async def get_products_callback(callback_query: types.CallbackQuery):
    """ЕЕЕЕЕЕЕЕЕЕЕЕЕМООООООООООООООООООЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕ"""
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

    await bot.send_message(callback_query.from_user.id, reviews_str, parse_mode='markdown')


"""aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaanтсюда"""


@dp.callback_query_handler(lambda msg: msg.text == "Локация")
def get_address_from_coords(update, context):
    # получаем обьект сообщения (локации)
    message = update.message
    # вытаскиваем из него долготу и ширину
    current_position = (message.location.longitude, message.location.latitude)
    # создаем строку в виде ДОЛГОТА,ШИРИНА
    coords = f"{current_position[0]},{current_position[1]}"
    # отправляем координаты в нашу функцию получения адреса
    address_str = get_address_from_coords(coords)
    # вовщращаем результат пользователю в боте
    update.message.reply_text(address_str)

    PARAMS = {
        "apikey": "ваш api key",
        "format": "json",
        "lang": "ru_RU",
        "kind": "house",
        "geocode": coords
    }

    # отправляем запрос по адресу геокодера.
    try:
        r = requests.get(url="https://geocode-maps.yandex.ru/1.x/", params=PARAMS)
        json_data = r.json()
        address_str = json_data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"][
            "GeocoderMetaData"]["AddressDetails"]["Country"]["AddressLine"]
        return address_str

    except Exception as e:
        # единственное что тут изменилось, так это сообщение об ошибке.
        return "Не могу определить адрес по этой локации/координатам.\n\nОтправь мне локацию или координаты (долгота, широта):"

    # Эта функция будет использоваться, если пользователь послал локацию.



if __name__ == '__main__':
    executor.start_polling(dp)
