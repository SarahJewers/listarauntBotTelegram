from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardButton, KeyboardButton
from aiogram.utils import executor

from config import TOKEN
from models import DBManager


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
db = DBManager()


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply(
        "Привет!\n" \
        "Я помогу тебе найти ресторан на сегодня.\n" \
        "Чтобы начать напиши: /go" \
        )


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply(
        "Помогите\n" \
        "пожалуйста помогите.\n" \
        "Чтобы начать напиши: /go" \
        )



@dp.message_handler(commands=['go'])
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


@dp.callback_query_handler(lambda call: call.data and call.data.startswith('ctg_'))
async def get_products_callback(callback_query: types.CallbackQuery):
    """Выбирает все товары из определенной категории"""
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
    """Выбирает товар из категории"""
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




    answer = f'*Ресторан:*{product[1]}\n*Описание:*{product[2]}\n*Адрес:*\n{product[5]}\n*Телефон:*{product[7]}'
    await bot.send_photo(
        chat_id=callback_query.from_user.id,
        caption=answer,
        reply_markup=keyboard,
        photo=product[3],
        parse_mode='markdown')


if __name__ == '__main__':
    executor.start_polling(dp)
