import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ================ Налаштування ===================
# Вставте свій токен бота нижче
BOT_TOKEN = "7983993765:AAGu-NrdifmWMi_HlMVIZMvkwS8tpiJxXVU"

# Введіть ID адміністраторів через кому, наприклад:
ADMINS = {569585062,797671005} 
# ================================================

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Шлях до бази даних SQLite
DB_PATH = "employees.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees 
                 (id INTEGER PRIMARY KEY, bonus INTEGER, username TEXT)''')
    conn.commit()
    conn.close()

def add_employee_db(emp_id, bonus=0, username="Unknown"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO employees (id, bonus, username) VALUES (?, ?, ?)", (emp_id, bonus, username))
    conn.commit()
    conn.close()

def update_bonus_db(emp_id, bonus):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE employees SET bonus=? WHERE id=?", (bonus, emp_id))
    conn.commit()
    conn.close()

def remove_employee_db(emp_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM employees WHERE id=?", (emp_id,))
    conn.commit()
    conn.close()

def get_all_employees_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, bonus, username FROM employees")
    rows = c.fetchall()
    conn.close()
    return rows

def get_employee_db(emp_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, bonus, username FROM employees WHERE id=?", (emp_id,))
    row = c.fetchone()
    conn.close()
    return row

# Константи для станів розмови (ConversationHandler) в адмінпанелі
(ADMIN_MAIN, ADMIN_AWARD_SELECT, ADMIN_AWARD_ENTER, ADMIN_ADD, ADMIN_REMOVE) = range(5)


# ----- Обробник для команди /start -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Якщо користувач є адміністратором, показуємо адмінпанель
    if user_id in ADMINS:
        text = "Вітаємо, адміністратор! Обери, що бажаєш зробити:"
        keyboard = [
            [InlineKeyboardButton("Нарахування бонусів", callback_data="admin_award")],
            [InlineKeyboardButton("Додати співробітника", callback_data="admin_add")],
            [InlineKeyboardButton("Видалити співробітника", callback_data="admin_remove")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)

    # Якщо користувач є співробітником (перевірка по базі даних)
    elif get_employee_db(user_id) is not None:
        emp = get_employee_db(user_id)
        bonus = emp[1]  # індекс 1 відповідає бонусам
        text = f"Привіт, хочешь подивитись бонуси?\nУ тебе {bonus} бонусів."
        keyboard = [[InlineKeyboardButton("Мої бонуси", callback_data="show_bonus")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text("Вибач, але ти не маєш доступу до цього бота.")


# ----- CallbackQueryHandler для обробки натискань кнопок -----
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    # Обробка кнопок для співробітників
    if data == "show_bonus":
        emp = get_employee_db(user_id)
        bonus = emp[1] if emp is not None else 0
        text = f"Твої бонуси: {bonus}\nНатисни 'Назад' щоб повернутись."
        keyboard = [[InlineKeyboardButton("Назад", callback_data="back_employee")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

    elif data == "back_employee":
        emp = get_employee_db(user_id)
        bonus = emp[1] if emp is not None else 0
        text = f"Привіт, хочешь подивитись бонуси?\nУ тебе {bonus} бонусів."
        keyboard = [[InlineKeyboardButton("Мої бонуси", callback_data="show_bonus")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

    # Обробка кнопок для адміністраторів
    elif data == "admin_award":
        employees_list = get_all_employees_db()
        if not employees_list:
            await query.edit_message_text("Немає співробітників. Додай спочатку співробітника.")
            return ADMIN_MAIN
        text = "Виберіть співробітника для нарахування бонусів:"
        keyboard = []
        for emp_id, bonus, username in employees_list:
            button_text = f"{emp_id} - {username}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"award_{emp_id}")])
        keyboard.append([InlineKeyboardButton("Назад", callback_data="admin_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_AWARD_SELECT

    elif data.startswith("award_"):
        selected_id = int(data.split("_")[1])
        context.user_data["selected_employee"] = selected_id
        text = (
            f"Введіть кількість бонусів для співробітника {selected_id} "
            f"(введіть 0 для скидання бонусів):"
        )
        keyboard = [[InlineKeyboardButton("Назад", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_AWARD_ENTER

    elif data == "admin_add":
        text = "Введіть ID співробітника, якого потрібно додати:"
        keyboard = [[InlineKeyboardButton("Назад", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_ADD

    elif data == "admin_remove":
        text = "Введіть ID співробітника, якого потрібно видалити:"
        keyboard = [[InlineKeyboardButton("Назад", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_REMOVE

    elif data == "admin_back":
        text = "Адмін панель:\nОбери дію:"
        keyboard = [
            [InlineKeyboardButton("Нарахування бонусів", callback_data="admin_award")],
            [InlineKeyboardButton("Додати співробітника", callback_data="admin_add")],
            [InlineKeyboardButton("Видалити співробітника", callback_data="admin_remove")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return ADMIN_MAIN

    return ConversationHandler.END


# ----- Обробник введення бонусів (адмін: нарахування бонусів) -----
async def admin_award_enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        bonus_amount = int(user_input)
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть коректне число.")
        return ADMIN_AWARD_ENTER

    selected_employee = context.user_data.get("selected_employee")
    if selected_employee is None:
        await update.message.reply_text("Не вибрано співробітника. Спробуйте ще раз.")
        return ADMIN_MAIN

    update_bonus_db(selected_employee, bonus_amount)

    try:
        await context.bot.send_message(
            chat_id=selected_employee,
            text=f"Вам нараховано {bonus_amount} бонусів!!",
        )
    except Exception as e:
        logging.error(f"Не вдалося повідомити співробітника {selected_employee}: {e}")

    await update.message.reply_text(
        f"Бонуси для співробітника {selected_employee} оновлено до {bonus_amount}.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="admin_back")]]),
    )
    return ADMIN_MAIN


# ----- Обробник введення ID для додавання співробітника -----
async def admin_add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        new_emp_id = int(user_input)
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть коректний ID (число).")
        return ADMIN_ADD

    if get_employee_db(new_emp_id) is not None:
        await update.message.reply_text("Співробітник з цим ID вже існує.")
    else:
        try:
            chat = await context.bot.get_chat(new_emp_id)
            username = chat.username if chat.username else chat.first_name
        except Exception as e:
            logging.error(f"Не вдалося отримати інформацію для {new_emp_id}: {e}")
            username = "Unknown"
        add_employee_db(new_emp_id, 0, username)
        await update.message.reply_text(f"Новий працівник додан! {new_emp_id} - {username}")
    return ADMIN_MAIN


# ----- Обробник введення ID для видалення співробітника -----
async def admin_remove_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        rem_emp_id = int(user_input)
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть коректний ID (число).")
        return ADMIN_REMOVE

    if get_employee_db(rem_emp_id) is not None:
        remove_employee_db(rem_emp_id)
        await update.message.reply_text("Співробітник видалений!")
    else:
        await update.message.reply_text("Співробітник з цим ID не знайдений.")
    return ADMIN_MAIN


# ----- Обробник команди /cancel для скасування розмови -----
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операцію скасовано.")
    return ConversationHandler.END


# ----- Основна функція запуску бота -----
def main():
    init_db()  # Ініціалізація бази даних
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^(admin_award|admin_add|admin_remove)$")],
        states={
            ADMIN_MAIN: [CallbackQueryHandler(button_handler, pattern="^admin_back$")],
            ADMIN_AWARD_SELECT: [CallbackQueryHandler(button_handler, pattern="^award_")],
            ADMIN_AWARD_ENTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_award_enter)],
            ADMIN_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_employee)],
            ADMIN_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_remove_employee)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()


if __name__ == '__main__':
    main()
