import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("ОШИБКА: Токен не найден! Пропиши BOT_TOKEN в переменных окружения.")

bot = telebot.TeleBot(TOKEN)

DATA_FILE = os.getenv('DATA_PATH', 'shopping_list.json')

# ТВОИ АДМИНЫ
ADMIN_USERNAMES = ['nek_223'] 

# ЧЕРНЫЙ СПИСОК
BANNED_USERNAMES = ['imapulsed']

# --- Блок работы с данными ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# ТЕПЕРЬ shopping_list имеет формат: {"Мясо": ["Pasha", "Lekha"], "Уголь": ["Polina"]}
shopping_list = load_data()
# ------------------------------

def get_list_keyboard():
    markup = InlineKeyboardMarkup()
    for item, voters in shopping_list.items():
        count = len(voters) # Считаем количество людей в списке
        btn = InlineKeyboardButton(
            text=f"{item} ({count} ➕)", 
            callback_data=f"vote_{item}"
        )
        markup.add(btn)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "Дарова! Я бот для сбора списка на шашлыки. 🍖\n\n"
        "Команды:\n"
        "/add [продукт] — добавить свои хотелки\n"
        "/list — глянуть список и проголосовать (1 раз за позицию)\n\n"
        "👑 Админы:\n"
        "/del [продукт] — удалить позицию"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['add'])
def add_item(message):
    user = message.from_user.username
    if user in BANNED_USERNAMES:
        bot.reply_to(message, "Тебе доступ закрыт! 🚫")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Пример: /add Мясо")
        return
    
    item = args[1].strip().capitalize()
    
    if item in shopping_list:
        # Если продукт есть, проверяем, не голосовал ли уже этот юзер
        if user not in shopping_list[item]:
            shopping_list[item].append(user)
            bot.reply_to(message, f"«{item}» уже в списке, добавил твой голос!")
        else:
            bot.reply_to(message, f"Ты уже голосовал за «{item}»!")
    else:
        # Если продукта нет — создаем новый список с первым проголосовавшим
        shopping_list[item] = [user]
        bot.reply_to(message, f"Добавил «{item}» в список!")
    
    save_data(shopping_list)

@bot.message_handler(commands=['del', 'delete'])
def delete_item(message):
    if message.from_user.username not in ADMIN_USERNAMES:
        bot.reply_to(message, "Нет прав! 🚫")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2: return
    
    item = args[1].strip().capitalize()
    if item in shopping_list:
        del shopping_list[item] 
        save_data(shopping_list) 
        bot.reply_to(message, f"Удалил «{item}» 🗑️")

@bot.message_handler(commands=['list'])
def show_list(message):
    if not shopping_list:
        bot.reply_to(message, "Список пуст.")
        return
    
    bot.send_message(
        message.chat.id, 
        "Список (один голос от человека):", 
        reply_markup=get_list_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
def handle_vote(call):
    user = call.from_user.username
    
    if user in BANNED_USERNAMES:
        bot.answer_callback_query(call.id, "Бан! 🚫", show_alert=True)
        return

    item = call.data.split('vote_')[1]
    
    if item in shopping_list:
        # ПРОВЕРКА: Если юзернейм уже есть в списке проголосовавших за этот товар
        if user in shopping_list[item]:
            bot.answer_callback_query(call.id, "Брат, ты уже голосовал за это! 🛑", show_alert=True)
        else:
            # Добавляем юзера в список и сохраняем
            shopping_list[item].append(user)
            save_data(shopping_list)
            
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                reply_markup=get_list_keyboard()
            )
            bot.answer_callback_query(call.id, f"Твой голос за {item} принят!")
    else:
        bot.answer_callback_query(call.id, "Позиция уже удалена.")

if __name__ == '__main__':
    bot.infinity_polling()