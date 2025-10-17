from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Скачати відео"))
    kb.add(KeyboardButton("Інструкція"), KeyboardButton("Історія"))
    return kb

def back_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Назад"))
    return kb
