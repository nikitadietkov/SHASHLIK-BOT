import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("ОШИБКА: Токен не найден! Пропиши BOT_TOKEN в переменных окружения.")

bot = telebot.TeleBot(TOKEN)

DATA_FILE = os.getenv('DATA_PATH', 'shopping_list.json')

# ТВОИ АДМИНЫ (могут удалять)
ADMIN_USERNAMES = ['nek_223'] 

# 🛑 ЧЕРНЫЙ СПИСОК (не могут добавлять и голосовать)
# Вписывай юзернеймы вредителей без @
BANNED_USERNAMES = ['imapulsed']

# --- Блок работы с сохранением данных ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

shopping_list = load_data()
# ----------------------------------------

def get_list_keyboard():
    markup = InlineKeyboardMarkup()
    for item, votes in shopping_list.items():
        btn = InlineKeyboardButton(
            text=f"{item} ({votes} ➕)", 
            callback_data=f"vote_{item}"
        )
        markup.add(btn)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "Дарова! Я бот для сбора списка на шашлыки. 🍖\n\n"
        "Команды:\n"
        "/add [продукт] — добавить свои хотелки в список\n"
        "/list — посмотреть список и плюсануть то, что уже добавили\n\n"
        "👑 Для админов:\n"
        "/del [продукт] — удалить позицию из списка"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['add'])
def add_item(message):
    # 🛑 ПРОВЕРКА НА БАН-ЛИСТ ПРИ ДОБАВЛЕНИИ
    if message.from_user.username in BANNED_USERNAMES:
        bot.reply_to(message, "Сорян, но тебе запрещено добавлять продукты в список! 🚫")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Формат команды: /add Мясо")
        return
    
    item = args[1].strip().capitalize()
    
    if item in shopping_list:
        shopping_list[item] += 1
        bot.reply_to(message, f"«{item}» уже есть в списке, накинул +1 голос!")
    else:
        shopping_list[item] = 1
        bot.reply_to(message, f"Добавил «{item}» в список покупок!")
    
    save_data(shopping_list)

@bot.message_handler(commands=['del', 'delete'])
def delete_item(message):
    if message.from_user.username not in ADMIN_USERNAMES:
        bot.reply_to(message, "Брат, у тебя нет прав удалять продукты из списка! 🚫")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Формат команды: /del Мясо")
        return
    
    item = args[1].strip().capitalize()
    
    if item in shopping_list:
        del shopping_list[item] 
        save_data(shopping_list) 
        bot.reply_to(message, f"Удалил «{item}» из списка! 🗑️")
    else:
        bot.reply_to(message, f"Брат, «{item}» и так нет в списке.")

@bot.message_handler(commands=['list'])
def show_list(message):
    if not shopping_list:
        bot.reply_to(message, "Список пока пуст. Добавь что-то через команду /add")
        return
    
    bot.send_message(
        message.chat.id, 
        "Список на шашлындос (жми на продукт, чтобы плюсануть):", 
        reply_markup=get_list_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
def handle_vote(call):
    # 🛑 ПРОВЕРКА НА БАН-ЛИСТ ПРИ ГОЛОСОВАНИИ
    if call.from_user.username in BANNED_USERNAMES:
        # show_alert=True покажет всплывающее окно прямо по центру экрана
        bot.answer_callback_query(call.id, "Тебе запрещено голосовать! 🚫", show_alert=True)
        return

    item = call.data.split('vote_')[1]
    
    if item in shopping_list:
        shopping_list[item] += 1
        save_data(shopping_list)
        
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            reply_markup=get_list_keyboard()
        )
        bot.answer_callback_query(call.id, f"+1 за {item}!")
    else:
        bot.answer_callback_query(call.id, "Этого продукта уже нет в списке.")

if __name__ == '__main__':
    print("Бот запущен. Данные в безопасности...")
    bot.infinity_polling()