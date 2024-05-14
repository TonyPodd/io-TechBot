from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

from aiogram.utils.keyboard import InlineKeyboardBuilder

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Каталог')],
                                     [KeyboardButton(text='Баланс'), KeyboardButton(text='Контакты')],
                                     [KeyboardButton(text='Сканировать QR-код'),],
                                    [KeyboardButton(text="/cancel",)],
                                     
                                     ],
                           resize_keyboard=True,
                           input_field_placeholder='Выберите пункт меню...')



get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер',
                                                           request_contact=True)]],
                                 resize_keyboard=True)

admin_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Каталог",)],
    [KeyboardButton(text="Добавить товар",), KeyboardButton(text="Удалить товар",)],
    [KeyboardButton(text="Сгенерировать QR-код",)],
    [KeyboardButton(text="/cancel",)],
    
], resize_keyboard=True)

show_katalog = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Каталог', callback_data='show_katalog')],
    
])

add_item_true = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить', callback_data='save_item'), InlineKeyboardButton(text='Отмена', callback_data='cancel_add_item')],
])



