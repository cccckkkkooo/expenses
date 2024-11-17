import telebot
from telebot import types
from datetime import datetime

TOKEN = '7854555014:AAFMIUJbrGOOH-_KyipfJEfsIXH00WlkqXY'
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения баланса каждого пользователя
user_balances = {}


# Функция для загрузки данных из файла
def load_balances():
    try:
        with open('user_balances.txt', 'r') as file:
            balances = {}
            for line in file:
                chat_id, balance = line.strip().split(':')
                balances[int(chat_id)] = int(balance)
            return balances
    except FileNotFoundError:
        return {}


# Функция для сохранения данных в файл
def save_balances():
    with open('user_balances.txt', 'w') as file:
        for chat_id, balance in user_balances.items():
            file.write(f"{chat_id}:{balance}\n")


# Функция для записи операций в файл
def log_operation(chat_id, value, category):
    with open('transaction_log.txt', 'a') as log_file:
        timestamp = datetime.now().strftime('%d-%m-%Y')
        log_file.write(f"{timestamp} | Chat ID: {chat_id} | {value} | {category}\n")


# Функция для удаления операции из лога
def delete_operation_from_log(value, category):
    try:
        with open('transaction_log.txt', 'r') as log_file:
            lines = log_file.readlines()
        with open('transaction_log.txt', 'w') as log_file:
            for line in lines:
                if not (f"{value} | {category}" in line):
                    log_file.write(line)
    except FileNotFoundError:
        return "Файл логов не найден."


# Загрузка балансов при запуске
user_balances = load_balances()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id not in user_balances:
        user_balances[message.chat.id] = 0  # Инициализация баланса пользователя
        save_balances()
    bot.send_message(message.chat.id, "Я пикми")


@bot.message_handler(commands=['delete'])
def delete_record(message):
    # Бот запрашивает у пользователя сумму и категорию для удаления
    bot.send_message(message.chat.id,
                     "Введите сумму и категорию операции для удаления в формате:\n<сумма> <категория> (например, 300 Еда)")

    # Далее обработчик для получения ввода пользователя
    @bot.message_handler(func=lambda msg: True)
    def handle_delete_input(msg):
        try:
            value, category = msg.text.split()
            value = int(value)
            if value <= 0:
                bot.send_message(msg.chat.id, "Пожалуйста, отправьте положительное число.")
                return
            chat_id = msg.chat.id

            # Проверка баланса пользователя, чтобы не было отрицательного баланса
            if user_balances.get(chat_id, 0) < value:
                bot.send_message(msg.chat.id, "Недостаточно средств для удаления этой операции.")
                return

            # Удаление записи из лога
            delete_operation_from_log(value, category)

            # Вычитание суммы из баланса пользователя
            user_balances[chat_id] -= value
            save_balances()

            bot.send_message(msg.chat.id,
                             f"Операция на сумму {value} в категории {category} была удалена, баланс обновлен.")
        except ValueError:
            bot.send_message(msg.chat.id, "Неверный формат ввода. Пожалуйста, используйте формат: <сумма> <категория>.")

@bot.message_handler(commands=['txt'])
def send_files(message):
    try:
        with open('user_balances.txt', 'rb') as balance_file, open('transaction_log.txt', 'rb') as log_file:
            bot.send_document(message.chat.id, balance_file)
            bot.send_document(message.chat.id, log_file)
    except FileNotFoundError:
        bot.send_message(message.chat.id, "Файлы ещё не созданы или недоступны.")


@bot.message_handler(commands=['updatedb'])
def update_database(message):
    try:
        with open('transaction_log.txt', 'r') as log_file:
            # Send the file as a document
            log_file.seek(0)  # Ensure we're at the start of the file
            bot.send_document(message.chat.id, log_file)

        # Clear the file after sending
        with open('transaction_log.txt', 'w') as log_file:
            log_file.truncate(0)  # Clear the file contents

        bot.send_message(message.chat.id, "Файл transaction_log успешно очищен.")
    except FileNotFoundError:
        bot.send_message(message.chat.id, "Файл transaction_log не найден.")


@bot.message_handler(commands=['exp'])
def show_balances(message):
    if user_balances:
        balances_str = "\n".join([f"{balance}" for balance in user_balances.values()])
        bot.send_message(message.chat.id, f"\n{balances_str}")
    else:
        bot.send_message(message.chat.id, "Балансы пользователей отсутствуют.")

@bot.message_handler(func=lambda message: True)
def handle_budget(message):
    chat_id = message.chat.id
    try:
        # Попытка преобразовать сообщение в число
        value = int(message.text)
        if value <= 0:
            bot.send_message(chat_id, "Пожалуйста, отправьте положительное число.")
            return
        user_balances[chat_id] += value  # Обновление баланса
        save_balances()  # Сохранение изменений в файл

        # Создание инлайн-кнопок для выбора категории
        markup = types.InlineKeyboardMarkup()
        categories = ['Еда', 'Транспорт', 'Развлечения', 'Здоровье', 'Другое']
        for category in categories:
            button = types.InlineKeyboardButton(text=category, callback_data=f"{value}:{category}")
            markup.add(button)

        bot.send_message(chat_id, "Выберите категорию для этой операции:", reply_markup=markup)
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, отправьте корректное число (например, +300).")


@bot.callback_query_handler(func=lambda call: True)
def handle_category_selection(call):
    chat_id = call.message.chat.id
    value, category = call.data.split(":")
    log_operation(chat_id, value, category)  # Логирование операции с категорией
    bot.send_message(chat_id, f"Операция на сумму {value} сохранена в категории: {category}")


bot.polling()
