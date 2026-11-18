import os
import telebot
import sqlite3

# Берем токен из переменных окружения. 
# Если запускаете локально, временно вставьте свой токен в кавычки: TOKEN = 'ваш_токен'
TOKEN = os.environ.get('TOKEN', 'ВСТАВЬТЕ_ВАШ_ТОКЕН_СЮДА')
bot = telebot.TeleBot(TOKEN)

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        task_text TEXT,
                        status TEXT DEFAULT 'active'
                    )''')
    conn.commit()
    conn.close()

init_db()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = ("Привет! Я бот «Дедлайн-помощник».\n\n"
            "Я помогу тебе не забыть о важных делах.\n"
            "Вот мои команды:\n"
            "/add <текст задачи> — добавить задачу\n"
            "/list — показать активные задачи\n"
            "/done <номер задачи> — отметить задачу выполненной")
    bot.reply_to(message, text)

@bot.message_handler(commands=['add'])
def add_task(message):
    # Берем текст после команды /add
    task_text = message.text.replace('/add', '', 1).strip()
    
    if not task_text:
        bot.reply_to(message, "Напиши задачу после команды. Пример: `/add Купить хлеб`", parse_mode='Markdown')
        return

    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, task_text) VALUES (?, ?)", (message.chat.id, task_text))
    conn.commit()
    conn.close()
    
    bot.reply_to(message, f"Задача добавлена: _{task_text}_", parse_mode='Markdown')

@bot.message_handler(commands=['list'])
def list_tasks(message):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_text FROM tasks WHERE user_id = ? AND status = 'active'", (message.chat.id,))
    tasks = cursor.fetchall()
    conn.close()

    if not tasks:
        bot.reply_to(message, "У тебя нет активных задач. Отдыхай!")
        return

    response = "Твои активные задачи:\n\n"
    for task in tasks:
        response += f"`{task[0]}.` {task[1]}\n"
        
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['done'])
def done_task(message):
    try:
        # Получаем номер задачи из сообщения (например, /done 1)
        task_id = int(message.text.split()[1])
        
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        # Проверяем, что задача существует, принадлежит этому юзеру и активна
        cursor.execute("UPDATE tasks SET status = 'done' WHERE id = ? AND user_id = ? AND status = 'active'", (task_id, message.chat.id))
        
        if cursor.rowcount > 0:
            bot.reply_to(message, f"Задача #{task_id} выполнена! Молодец!")
        else:
            bot.reply_to(message, f"Задача #{task_id} не найдена или уже выполнена.")
            
        conn.commit()
        conn.close()
    except (IndexError, ValueError):
        bot.reply_to(message, "Используй формат: `/done <номер задачи>`. Например: `/done 1`", parse_mode='Markdown')

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()